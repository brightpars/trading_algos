from __future__ import annotations

from pathlib import Path

from flask import Flask
from pymongo import MongoClient

from trading_algos_dashboard.blueprints.algorithms import bp as algorithms_bp
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
from trading_algos_dashboard.repositories.result_repository import ResultRepository
from trading_algos_dashboard.services.algorithm_catalog_service import (
    list_algorithm_catalog,
)
from trading_algos_dashboard.services.data_source_service import (
    SmarttradeDataSourceService,
)
from trading_algos_dashboard.services.data_source_settings_service import (
    DataSourceSettingsService,
)
from trading_algos_dashboard.services.experiment_service import ExperimentService


def create_app(config: DashboardConfig | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    cfg = config or DashboardConfig.from_env()
    app.config.update(
        SECRET_KEY=cfg.secret_key,
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
    data_source_settings_repository = DataSourceSettingsRepository(mongo.db)
    data_source_settings_service = DataSourceSettingsService(
        repository=data_source_settings_repository
    )
    data_source_service = SmarttradeDataSourceService(
        smarttrade_path=cfg.smarttrade_path,
        user_id=cfg.smarttrade_user_id,
        endpoint_resolver=lambda: (
            data_source_settings_service.get_effective_settings()["ip"],
            data_source_settings_service.get_effective_settings()["port"],
        ),
    )
    experiment_service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=data_source_service,
        report_base_path=cfg.report_base_path,
    )

    app.extensions["mongo"] = mongo
    app.extensions["experiment_repository"] = experiment_repository
    app.extensions["result_repository"] = result_repository
    app.extensions["data_source_settings_repository"] = data_source_settings_repository
    app.extensions["data_source_settings_service"] = data_source_settings_service
    app.extensions["data_source_service"] = data_source_service
    app.extensions["experiment_service"] = experiment_service
    app.extensions["algorithm_catalog_service"] = list_algorithm_catalog

    app.register_blueprint(home_bp)
    app.register_blueprint(algorithms_bp)
    app.register_blueprint(experiments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    return app
