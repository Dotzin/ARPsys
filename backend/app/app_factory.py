from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import fastapi.encoders
from contextlib import asynccontextmanager
from app.routes.relatorio_routes import router as relatorio_router
from app.routes.orders_routes import router as orders_router
from app.routes.sku_nicho_routes import router as sku_nicho_router
from app.routes.auth_routes import router as auth_router
from app.routes.websocket_routes import router as websocket_router
from app.routes.integrations_routes import router as integrations_router
from app.core.container import Container
from app.config.settings import settings
from app.background_tasks.periodic_report_task import BackgroundTaskService
from dependency_injector import providers
import logging
import numpy as np
import json

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def numpy_encoder(obj):
    """Custom encoder for numpy types"""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Monkey patch jsonable_encoder to handle numpy types
_original_jsonable_encoder = fastapi.encoders.jsonable_encoder

def patched_jsonable_encoder(obj, **kwargs):
    """Patched jsonable_encoder that handles numpy types"""
    # Handle numpy types first
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # For other types, use original encoder
    return _original_jsonable_encoder(obj, **kwargs)

fastapi.encoders.jsonable_encoder = patched_jsonable_encoder


class NumpyJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=numpy_encoder,
        ).encode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando aplicação FastAPI")
    app.state.background_task_service.start()

    # Calculate initial report
    report_service = app.state.container.report_service()
    initial_report = report_service.get_daily_report_data()
    if initial_report:
        app.state.current_daily_report = initial_report
        logger.info("Relatório inicial calculado")

    yield

    # Shutdown
    logger.info("Encerrando aplicação FastAPI")
    app.state.background_task_service.stop()
    try:
        app.state.database_service.close()
    except AttributeError:
        pass


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This function initializes all services using dependency injection,
    mounts static files, and includes all routers.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    app = FastAPI(lifespan=lifespan, default_response_class=NumpyJSONResponse)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://refactored-disco-qwjwpq775v93xvv9-3000.app.github.dev"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize dependency container
    container = Container()
    container.wire(modules=[
        "app.routes.auth_routes",
        "app.routes.relatorio_routes",
        "app.routes.orders_routes",
        "app.routes.sku_nicho_routes",
        "app.routes.websocket_routes",
        "app.routes.integrations_routes",
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
    app.include_router(auth_router, prefix="/auth", tags=["authentication"])
    app.include_router(relatorio_router)
    app.include_router(orders_router)
    app.include_router(sku_nicho_router)
    app.include_router(websocket_router)
    app.include_router(integrations_router, prefix="/integrations", tags=["integrations"])

    logger.info("App criado e configurado com sucesso")
    return app
