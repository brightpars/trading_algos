from __future__ import annotations

from pathlib import Path

from flask import Flask
from pymongo import MongoClient

from trading_algos_dashboard.blueprints.algorithms import bp as algorithms_bp
from trading_algos_dashboard.blueprints.administration import bp as administration_bp
from trading_algos_dashboard.blueprints.configurations import bp as configurations_bp
from trading_algos_dashboard.blueprints.api import bp as api_bp
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
from trading_algos_dashboard.repositories.publication_record_repository import (
    PublicationRecordRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository
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
    SmarttradeDataSourceService,
)
from trading_algos_dashboard.services.data_source_settings_service import (
    DataSourceSettingsService,
)
from trading_algos_dashboard.services.configuration_builder_service import (
    ConfigurationBuilderService,
)
from trading_algos_dashboard.services.configuration_publish_service import (
    ConfigurationPublishService,
)
from trading_algos_dashboard.services.experiment_service import ExperimentService
from trading_algos_dashboard.services.market_data_cache import InMemoryMarketDataCache
from trading_algos_dashboard.services.report_service import ReportService


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
        SMARTTRADE_PATH=cfg.smarttrade_path,
        SMARTTRADE_USER_ID=cfg.smarttrade_user_id,
    )

    mongo.client = MongoClient(cfg.mongo_uri)
    mongo.db = mongo.client[cfg.mongo_db_name]

    experiment_repository = ExperimentRepository(mongo.db)
    result_repository = ResultRepository(mongo.db)
    configuration_draft_repository = ConfigurationDraftRepository(mongo.db)
    configuration_revision_repository = ConfigurationRevisionRepository(mongo.db)
    publication_record_repository = PublicationRecordRepository(mongo.db)
    data_source_settings_repository = DataSourceSettingsRepository(mongo.db)
    algorithm_catalog_repository = AlgorithmCatalogRepository(mongo.db)
    algorithm_catalog_import_run_repository = AlgorithmCatalogImportRunRepository(
        mongo.db
    )
    data_source_settings_service = DataSourceSettingsService(
        repository=data_source_settings_repository
    )
    market_data_cache = InMemoryMarketDataCache(enabled=True)
    data_source_service = SmarttradeDataSourceService(
        smarttrade_path=cfg.smarttrade_path,
        user_id=cfg.smarttrade_user_id,
        endpoint_resolver=lambda: (
            data_source_settings_service.get_effective_settings()["ip"],
            data_source_settings_service.get_effective_settings()["port"],
        ),
        market_data_cache=market_data_cache,
    )
    experiment_service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=data_source_service,
        report_base_path=cfg.report_base_path,
    )
    algorithm_catalog_service = AlgorithmCatalogService(
        catalog_repository=algorithm_catalog_repository,
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
    configuration_builder_service = ConfigurationBuilderService(
        draft_repository=configuration_draft_repository,
        revision_repository=configuration_revision_repository,
        publication_record_repository=publication_record_repository,
    )
    configuration_publish_service = ConfigurationPublishService(
        publication_record_repository=publication_record_repository,
        base_url=cfg.smarttrade_api_base_url,
        token=cfg.smarttrade_api_token,
        timeout_secs=cfg.smarttrade_api_timeout_secs,
    )

    app.extensions["mongo"] = mongo
    app.extensions["experiment_repository"] = experiment_repository
    app.extensions["result_repository"] = result_repository
    app.extensions["configuration_draft_repository"] = configuration_draft_repository
    app.extensions["configuration_revision_repository"] = (
        configuration_revision_repository
    )
    app.extensions["publication_record_repository"] = publication_record_repository
    app.extensions["data_source_settings_repository"] = data_source_settings_repository
    app.extensions["algorithm_catalog_repository"] = algorithm_catalog_repository
    app.extensions["algorithm_catalog_import_run_repository"] = (
        algorithm_catalog_import_run_repository
    )
    app.extensions["data_source_settings_service"] = data_source_settings_service
    app.extensions["market_data_cache"] = market_data_cache
    app.extensions["data_source_service"] = data_source_service
    app.extensions["experiment_service"] = experiment_service
    app.extensions["administration_service"] = administration_service
    app.extensions["algorithm_catalog_service"] = algorithm_catalog_service
    app.extensions["algorithm_catalog_import_service"] = (
        algorithm_catalog_import_service
    )
    app.extensions["report_service"] = report_service
    app.extensions["configuration_builder_service"] = configuration_builder_service
    app.extensions["configuration_publish_service"] = configuration_publish_service

    app.register_blueprint(home_bp)
    app.register_blueprint(algorithms_bp)
    app.register_blueprint(administration_bp)
    app.register_blueprint(configurations_bp)
    app.register_blueprint(experiments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    return app
