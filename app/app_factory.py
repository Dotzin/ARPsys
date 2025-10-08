from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.routes.relatorio_routes import router as relatorio_router
from app.routes.orders_routes import router as orders_router
from app.routes.sku_nicho_routes import router as sku_nicho_router
from app.routes.websocket_routes import router as websocket_router
from app.core.container import Container
from app.config.settings import settings
from app.background_tasks.periodic_report_task import BackgroundTaskService
from dependency_injector import providers
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This function initializes all services using dependency injection,
    mounts static files, and includes all routers.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    app = FastAPI(lifespan=lifespan)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Initialize dependency container
    container = Container()
    container.wire(modules=[
        "app.routes.relatorio_routes",
        "app.routes.orders_routes",
        "app.routes.sku_nicho_routes",
        "app.routes.websocket_routes",
    ])

    # Override providers that need app instance
    container.background_task_service.override(
        providers.Singleton(
            BackgroundTaskService,
            app=providers.Object(app),
            manager=container.connection_manager(),
            report_service=container.report_service(),
            update_interval_seconds=settings.report_update_interval,
        )
    )

    # Get services from container
    database_service = container.database_service()
    database_service.connect()
    database_service.create_tables()

    # Get background task service and store in app state
    background_task_service = container.background_task_service()
    app.state.background_task_service = background_task_service

    # Store container in app state for access if needed
    app.state.container = container

    # Include routers
    app.include_router(relatorio_router)
    app.include_router(orders_router)
    app.include_router(sku_nicho_router)
    app.include_router(websocket_router)

    logger.info("App criado e configurado com sucesso")
    return app
