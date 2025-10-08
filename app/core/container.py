from dependency_injector import containers, providers
from app.config.settings import settings
from app.services.database_service import DatabaseService
from app.services.report_service import ReportService
from app.services.order_service import OrderInserter
from app.services.sku_nicho_service import SkuNichoInserter
from app.core.connection_manager import ConnectionManager
from app.background_tasks.periodic_report_task import BackgroundTaskService


class Container(containers.DeclarativeContainer):
    pass

    # Configuration
    config = providers.Object(settings)

    # Services
    database_service = providers.Singleton(
        DatabaseService,
        db_path=config.provided.database_path,
    )

    report_service = providers.Singleton(
        ReportService,
        database=database_service.provided.database,
    )

    order_inserter = providers.Singleton(
        OrderInserter,
        database=database_service.provided.database,
    )

    sku_nicho_inserter = providers.Singleton(
        SkuNichoInserter,
        database=database_service.provided.database,
    )

    connection_manager = providers.Singleton(
        ConnectionManager,
        logger=providers.Object(None),  # Will be set later or use logging
    )

    database = providers.Singleton(
        lambda db_service: db_service.database,
        db_service=database_service,
    )

    background_task_service = providers.Singleton(
        BackgroundTaskService,
        app=providers.Object(None),  # Will be set in app_factory
        manager=connection_manager,
        report_service=report_service,
        update_interval_seconds=config.provided.report_update_interval,
    )


# Create container instance
container = Container()
