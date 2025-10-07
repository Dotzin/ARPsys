from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.routes.relatorio_routes import router as relatorio_router
from app.routes.orders_routes import router as orders_router
from app.routes.sku_nicho_routes import router as sku_nicho_router
from app.routes.websocket_routes import router as websocket_router
from app.services.database_service import DatabaseService
from app.services.report_service import ReportService
from app.services.order_service import OrderInserter
from app.services.sku_nicho_service import SkuNichoInserter
from app.core.connection_manager import ConnectionManager
from app.background_tasks.periodic_report_task import BackgroundTaskService
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando aplicação FastAPI")
    app.state.background_task_service.start()

    # Calculate initial report
    initial_report = app.state.report_service.get_daily_report_data()
    if initial_report:
        app.state.current_daily_report = initial_report
        logger.info("Relatório inicial calculado")

    yield

    # Shutdown
    logger.info("Encerrando aplicação FastAPI")
    app.state.background_task_service.stop()
    app.state.database_service.close()

# Função para criar e configurar o app FastAPI
def create_app():
    app = FastAPI(lifespan=lifespan)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Initialize database service
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "database.db")
    database_service = DatabaseService(db_path)
    database_service.connect()
    database_service.create_tables()

    # Initialize services
    report_service = ReportService(database_service.database)
    order_inserter = OrderInserter(database_service.database)
    sku_nicho_inserter = SkuNichoInserter(database_service.database)
    connection_manager = ConnectionManager(logger)

    # Store services in app state for dependency injection
    app.state.database_service = database_service
    app.state.report_service = report_service
    app.state.order_inserter = order_inserter
    app.state.sku_nicho_inserter = sku_nicho_inserter
    app.state.connection_manager = connection_manager

    # Override dependency functions to use app state
    from app.routes.relatorio_routes import get_order_inserter, get_report_service, get_connection_manager
    from app.routes.sku_nicho_routes import get_sku_nicho_inserter
    from app.routes.orders_routes import get_database
    from app.routes.websocket_routes import get_connection_manager as get_ws_manager, get_report_service as get_ws_report

    def _get_order_inserter():
        return app.state.order_inserter

    def _get_report_service():
        return app.state.report_service

    def _get_connection_manager():
        return app.state.connection_manager

    def _get_sku_nicho_inserter():
        return app.state.sku_nicho_inserter

    def _get_database():
        return app.state.database_service.database

    # Services are now injected via app.state in dependency functions

    # Include routers
    app.include_router(relatorio_router)
    app.include_router(orders_router)
    app.include_router(sku_nicho_router)
    app.include_router(websocket_router)

    # Initialize background task service (will be started in lifespan)
    background_task_service = BackgroundTaskService(app, connection_manager, report_service)
    app.state.background_task_service = background_task_service

    logger.info("App criado e configurado com sucesso")
    return app
