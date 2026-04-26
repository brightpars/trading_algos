from __future__ import annotations

from pathlib import Path

from flask import Flask
from pymongo import MongoClient

from trading_algos_dashboard.blueprints.algorithms import bp as algorithms_bp
from trading_algos_dashboard.blueprints.administration import bp as administration_bp
from trading_algos_dashboard.blueprints.configurations import bp as configurations_bp
from trading_algos_dashboard.blueprints.api import bp as api_bp
from trading_algos_dashboard.blueprints.evaluations import bp as evaluations_bp
from trading_algos_dashboard.blueprints.experiments import bp as experiments_bp
from trading_algos_dashboard.blueprints.home import bp as home_bp
from trading_algos_dashboard.blueprints.reports import bp as reports_bp
from trading_algos_dashboard.config import DashboardConfig
from trading_algos_dashboard.extensions import mongo
from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)
from trading_algos_dashboard.repositories.data_source_settings_repository import (
    DataSourceSettingsRepository,
)
from trading_algos_dashboard.repositories.configuration_draft_repository import (
    ConfigurationDraftRepository,
)
from trading_algos_dashboard.repositories.configuration_revision_repository import (
    ConfigurationRevisionRepository,
)
from trading_algos_dashboard.repositories.algorithm_catalog_import_run_repository import (
    AlgorithmCatalogImportRunRepository,
)
from trading_algos_dashboard.repositories.algorithm_catalog_repository import (
    AlgorithmCatalogRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository
from trading_algos_dashboard.repositories.backtrace_session_repository import (
    BacktraceSessionRepository,
)
from trading_algos_dashboard.repositories.market_data_cache_repository import (
    MarketDataCacheRepository,
)
from trading_algos_dashboard.repositories.market_data_cache_settings_repository import (
    MarketDataCacheSettingsRepository,
)
from trading_algos_dashboard.repositories.experiment_runtime_settings_repository import (
    ExperimentRuntimeSettingsRepository,
)
from trading_algos_dashboard.repositories.experiment_scheduler_lease_repository import (
    ExperimentSchedulerLeaseRepository,
)
from trading_algos_dashboard.repositories.server_control_settings_repository import (
    ServerControlSettingsRepository,
)
from trading_algos_dashboard.services.algorithm_catalog_service import (
    AlgorithmCatalogService,
)
from trading_algos_dashboard.services.algorithm_catalog_import_service import (
    AlgorithmCatalogImportService,
)
from trading_algos_dashboard.services.administration_service import (
    AdministrationService,
)
from trading_algos_dashboard.services.data_source_service import (
    MarketDataSourceService,
)
from trading_algos_dashboard.services.data_source_settings_service import (
    DataSourceSettingsService,
)
from trading_algos_dashboard.services.configuration_builder_service import (
    ConfigurationBuilderService,
)
from trading_algos_dashboard.services.experiment_service import ExperimentService
from trading_algos_dashboard.services.bulk_experiment_service import (
    BulkExperimentService,
)
from trading_algos_dashboard.services.cache_management_service import (
    CacheManagementService,
)
from trading_algos_dashboard.services.evaluation_service import EvaluationService
from trading_algos_dashboard.services.experiment_runtime_settings_service import (
    ExperimentRuntimeSettingsService,
)
from trading_algos_dashboard.services.experiment_scheduler_lease_service import (
    ExperimentSchedulerLeaseService,
)
from trading_algos_dashboard.services.market_data_cache import (
    InMemoryMarketDataCache,
    LayeredMarketDataCache,
    MongoMarketDataCache,
)
from trading_algos_dashboard.services.market_data_cache_settings_service import (
    MarketDataCacheSettingsService,
)
from trading_algos_dashboard.services.report_service import ReportService
from trading_algos_dashboard.services.server_control_service import ServerControlService
from trading_algos_dashboard.services.backtrace_client_service import (
    BacktraceClientService,
)
from trading_algos_dashboard.services.engines_control_runtime_service import (
    EnginesControlRuntimeService,
)


def create_app(config: DashboardConfig | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    cfg = config or DashboardConfig.from_env()
    app.config.update(
        SECRET_KEY=cfg.secret_key,
        SESSION_COOKIE_NAME="trading_algos_session",
        MONGO_URI=cfg.mongo_uri,
        MONGO_DB_NAME=cfg.mongo_db_name,
        REPORT_BASE_PATH=cfg.report_base_path,
        EXPERIMENT_MAX_CONCURRENT_RUNS=cfg.experiment_max_concurrent_runs,
    )

    mongo.client = MongoClient(cfg.mongo_uri)
    mongo.db = mongo.client[cfg.mongo_db_name]

    experiment_repository = ExperimentRepository(mongo.db)
    result_repository = ResultRepository(mongo.db)
    backtrace_session_repository = BacktraceSessionRepository(mongo.db)
    configuration_draft_repository = ConfigurationDraftRepository(mongo.db)
    configuration_revision_repository = ConfigurationRevisionRepository(mongo.db)
    data_source_settings_repository = DataSourceSettingsRepository(mongo.db)
    algorithm_catalog_repository = AlgorithmCatalogRepository(mongo.db)
    market_data_cache_repository = MarketDataCacheRepository(mongo.db)
    market_data_cache_settings_repository = MarketDataCacheSettingsRepository(mongo.db)
    experiment_runtime_settings_repository = ExperimentRuntimeSettingsRepository(
        mongo.db
    )
    experiment_scheduler_lease_repository = ExperimentSchedulerLeaseRepository(mongo.db)
    server_control_settings_repository = ServerControlSettingsRepository(mongo.db)
    algorithm_catalog_import_run_repository = AlgorithmCatalogImportRunRepository(
        mongo.db
    )
    data_source_settings_service = DataSourceSettingsService(
        repository=data_source_settings_repository
    )
    experiment_runtime_settings_service = ExperimentRuntimeSettingsService(
        repository=experiment_runtime_settings_repository,
        default_max_concurrent_experiments=cfg.experiment_max_concurrent_runs,
    )
    experiment_scheduler_lease_service = ExperimentSchedulerLeaseService(
        repository=experiment_scheduler_lease_repository,
    )
    market_data_cache_settings_service = MarketDataCacheSettingsService(
        repository=market_data_cache_settings_repository,
    )
    cache_settings = market_data_cache_settings_service.get_effective_settings()
    market_data_cache = LayeredMarketDataCache(
        memory_cache=InMemoryMarketDataCache(
            enabled=cache_settings["memory_enabled"],
            max_entries=cache_settings["memory_max_entries"],
        ),
        shared_cache=MongoMarketDataCache(
            repository=market_data_cache_repository,
            enabled=cache_settings["shared_enabled"],
            max_entries=cache_settings["shared_max_entries"],
            ttl_hours=cache_settings["shared_ttl_hours"],
        ),
    )
    data_source_service = MarketDataSourceService(
        endpoint_resolver=lambda: (
            data_source_settings_service.get_effective_settings()["ip"],
            data_source_settings_service.get_effective_settings()["port"],
        ),
        market_data_cache=market_data_cache,
    )
    cache_management_service = CacheManagementService(
        market_data_cache=market_data_cache,
        data_source_service=data_source_service,
    )
    experiment_service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=data_source_service,
        report_base_path=cfg.report_base_path,
        max_concurrent_experiments=cfg.experiment_max_concurrent_runs,
        max_concurrent_experiments_provider=lambda: (
            experiment_runtime_settings_service.get_effective_settings()[
                "max_concurrent_experiments"
            ]
        ),
        scheduler_lease_manager=experiment_scheduler_lease_service,
    )
    algorithm_catalog_service = AlgorithmCatalogService(
        catalog_repository=algorithm_catalog_repository,
    )
    bulk_experiment_service = BulkExperimentService(
        experiment_service=experiment_service,
        algorithm_catalog_service=algorithm_catalog_service,
    )
    administration_service = AdministrationService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        algorithm_catalog_repository=algorithm_catalog_repository,
        algorithm_catalog_import_run_repository=algorithm_catalog_import_run_repository,
        algorithm_catalog_service=algorithm_catalog_service,
    )
    algorithm_catalog_import_service = AlgorithmCatalogImportService(
        catalog_repository=algorithm_catalog_repository,
        import_run_repository=algorithm_catalog_import_run_repository,
    )
    administration_service.rebuild_algorithm_catalog_links()
    report_service = ReportService(result_repository=result_repository)
    evaluation_service = EvaluationService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
    )
    configuration_builder_service = ConfigurationBuilderService(
        draft_repository=configuration_draft_repository,
        revision_repository=configuration_revision_repository,
    )
    server_control_service = ServerControlService(
        repository=server_control_settings_repository,
    )
    engines_control_runtime_service = EnginesControlRuntimeService(
        backtrace_session_repository=backtrace_session_repository,
    )
    backtrace_client_service = BacktraceClientService(
        runtime_service=engines_control_runtime_service,
        backtrace_session_repository=backtrace_session_repository,
    )

    app.extensions["mongo"] = mongo
    app.extensions["experiment_repository"] = experiment_repository
    app.extensions["result_repository"] = result_repository
    app.extensions["backtrace_session_repository"] = backtrace_session_repository
    app.extensions["configuration_draft_repository"] = configuration_draft_repository
    app.extensions["configuration_revision_repository"] = (
        configuration_revision_repository
    )
    app.extensions["data_source_settings_repository"] = data_source_settings_repository
    app.extensions["algorithm_catalog_repository"] = algorithm_catalog_repository
    app.extensions["market_data_cache_repository"] = market_data_cache_repository
    app.extensions["market_data_cache_settings_repository"] = (
        market_data_cache_settings_repository
    )
    app.extensions["experiment_runtime_settings_repository"] = (
        experiment_runtime_settings_repository
    )
    app.extensions["experiment_scheduler_lease_repository"] = (
        experiment_scheduler_lease_repository
    )
    app.extensions["server_control_settings_repository"] = (
        server_control_settings_repository
    )
    app.extensions["algorithm_catalog_import_run_repository"] = (
        algorithm_catalog_import_run_repository
    )
    app.extensions["data_source_settings_service"] = data_source_settings_service
    app.extensions["experiment_runtime_settings_service"] = (
        experiment_runtime_settings_service
    )
    app.extensions["experiment_scheduler_lease_service"] = (
        experiment_scheduler_lease_service
    )
    app.extensions["market_data_cache"] = market_data_cache
    app.extensions["market_data_cache_settings_service"] = (
        market_data_cache_settings_service
    )
    app.extensions["data_source_service"] = data_source_service
    app.extensions["cache_management_service"] = cache_management_service
    app.extensions["experiment_service"] = experiment_service
    app.extensions["bulk_experiment_service"] = bulk_experiment_service
    app.extensions["administration_service"] = administration_service
    app.extensions["algorithm_catalog_service"] = algorithm_catalog_service
    app.extensions["algorithm_catalog_import_service"] = (
        algorithm_catalog_import_service
    )
    app.extensions["report_service"] = report_service
    app.extensions["evaluation_service"] = evaluation_service
    app.extensions["configuration_builder_service"] = configuration_builder_service
    app.extensions["server_control_service"] = server_control_service
    app.extensions["engines_control_runtime_service"] = engines_control_runtime_service
    app.extensions["backtrace_client_service"] = backtrace_client_service

    app.register_blueprint(home_bp)
    app.register_blueprint(algorithms_bp)
    app.register_blueprint(administration_bp)
    app.register_blueprint(configurations_bp)
    app.register_blueprint(experiments_bp)
    app.register_blueprint(evaluations_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    return app
