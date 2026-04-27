from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mongoengine  # type: ignore[import-untyped]
from pymongo import MongoClient
from pymongo.database import Database
from trading_servers import CentralServer
from trading_servers import DataServer
from trading_servers.engines_control import Server as EnginesControlServer
from trading_servers import FakeDateTimeServer
from trading_servers.xmlrpc_server import Base_XML_RPC_Server


@dataclass(frozen=True)
class ServiceRuntimeConfig:
    name: str
    host: str
    port: int
    user_id: int


class MongoCounterRepository:
    def __init__(self, *, mongo_uri: str, mongo_db_name: str) -> None:
        self._client: MongoClient[Any] = MongoClient(mongo_uri)
        self._db: Database[Any] = self._client[mongo_db_name]
        self._collection = self._db["dashboard_service_runtime_counters"]

    def get_counter_seed_value(self, counter_name: str) -> int:
        document = self._collection.find_one({"_id": counter_name}) or {}
        return int(document.get("seq", 0))

    def get_next_counter_value(self, counter_name: str, seed_value: int) -> int:
        self._collection.update_one(
            {"_id": counter_name},
            {"$set": {"seq": int(seed_value)}, "$inc": {"seq": 1}},
            upsert=True,
        )
        refreshed = self._collection.find_one({"_id": counter_name}) or {}
        return int(refreshed.get("seq", seed_value + 1))


def _build_config() -> ServiceRuntimeConfig:
    return ServiceRuntimeConfig(
        name=os.environ["SERVICE_NAME"].strip(),
        host=os.environ["SERVICE_HOST"].strip(),
        port=int(os.environ["SERVICE_PORT"]),
        user_id=int(os.environ.get("SERVICE_USER_ID", "1")),
    )


def _mongo_runtime_settings() -> tuple[str, str]:
    return (
        os.environ.get(
            "TRADING_ALGOS_DASHBOARD_MONGO_URI", "mongodb://127.0.0.1:27017"
        ),
        os.environ.get("TRADING_ALGOS_DASHBOARD_MONGO_DB", "trading_algos_dashboard"),
    )


def _mongoengine_host_string() -> str:
    mongo_uri, mongo_db_name = _mongo_runtime_settings()
    base_uri = mongo_uri.strip() or "mongodb://127.0.0.1:27017"
    if "/" in base_uri.removeprefix("mongodb://"):
        return base_uri
    return f"{base_uri.rstrip('/')}/{mongo_db_name}"


def _connect_data_runtime_storage() -> None:
    try:
        mongoengine.disconnect()
    except Exception:
        pass
    mongoengine.connect(
        host=_mongoengine_host_string(),
        connect=False,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
        socketTimeoutMS=5000,
        uuidRepresentation="standard",
    )


def _smarttrade_repo_root() -> Path:
    return Path(__file__).resolve().parents[3] / "smarttrade"


def _ensure_smarttrade_import_paths() -> None:
    src_root = str(Path(__file__).resolve().parents[1])
    smarttrade_root = str(_smarttrade_repo_root())
    for path in [src_root, smarttrade_root]:
        if path not in sys.path:
            sys.path.insert(0, path)


def _configure_engines_control_runtime() -> None:
    _ensure_smarttrade_import_paths()

    from config.service import get_config_service  # type: ignore[import-not-found]
    from engines.alertgen.alertgen_algs import AlertGenAlgs  # type: ignore[import-not-found]
    from engines.decmaker.decmaker_algs import DecMakerAlgs  # type: ignore[import-not-found]
    from trading_servers.engines_control_runtime import (  # type: ignore[import-not-found]
        EnginesControlRuntimeDependencies,
        configure_engines_control_runtime,
    )
    from utils_shared.helpers import (  # type: ignore[import-not-found]
        validate_alertgen_engine_payload,
        validate_decmaker_engine_payload,
    )
    from utils_shared.helpers_basic import custom_sleep  # type: ignore[import-not-found]
    from utils_shared.logging import log_debug, log_error  # type: ignore[import-not-found]
    from utils_shared.online_services import (  # type: ignore[import-not-found]
        get_server_state_by_proxy,
    )
    from utils_shared.objects_factory.broker_proxy import (  # type: ignore[import-not-found]
        get_or_create_broker_proxy,
    )
    from utils_shared.objects_factory.central_proxy import (  # type: ignore[import-not-found]
        get_or_create_central_proxy,
    )
    from utils_shared.objects_factory.data_proxy import (  # type: ignore[import-not-found]
        get_or_create_data_proxy,
    )
    from utils_shared.objects_factory.date_time_proxy import (  # type: ignore[import-not-found]
        get_or_create_fake_datetime_proxy,
    )

    configure_engines_control_runtime(
        EnginesControlRuntimeDependencies(
            decmaker_class=DecMakerAlgs,
            alertgen_class=AlertGenAlgs,
            get_config_service=get_config_service,
            get_server_state_by_proxy=get_server_state_by_proxy,
            custom_sleep=custom_sleep,
            log_debug=log_debug,
            log_error=log_error,
            get_central_proxy=get_or_create_central_proxy,
            get_fake_datetime_proxy=get_or_create_fake_datetime_proxy,
            get_data_proxy=get_or_create_data_proxy,
            get_broker_proxy=get_or_create_broker_proxy,
            validate_alertgen_engine_payload=validate_alertgen_engine_payload,
            validate_decmaker_engine_payload=validate_decmaker_engine_payload,
        )
    )


def _build_server(config: ServiceRuntimeConfig) -> Base_XML_RPC_Server:
    if config.name == "central":
        mongo_uri, mongo_db_name = _mongo_runtime_settings()
        return CentralServer(
            user_id=config.user_id,
            ip=config.host,
            port=config.port,
            sever_name=config.name,
            log_requests_to_terminal=False,
            counter_repository=MongoCounterRepository(
                mongo_uri=mongo_uri,
                mongo_db_name=mongo_db_name,
            ),
        )
    if config.name == "data":
        _connect_data_runtime_storage()
        return DataServer(
            user_id=config.user_id,
            ip=config.host,
            port=config.port,
            sever_name=config.name,
            log_requests_to_terminal=False,
        )
    if config.name == "fake_datetime":
        return FakeDateTimeServer(
            user_id=config.user_id,
            ip=config.host,
            port=config.port,
            sever_name=config.name,
            log_requests_to_terminal=False,
        )
    if config.name == "engines_control":
        _configure_engines_control_runtime()
        return EnginesControlServer(
            user_id=config.user_id,
            ip=config.host,
            port=config.port,
            sever_name=config.name,
            log_requests_to_terminal=False,
        )
    raise ValueError(f"Unsupported service runtime: {config.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("service_name")
    args = parser.parse_args()
    os.environ["SERVICE_NAME"] = args.service_name
    config = _build_config()
    server = _build_server(config)
    server.run_blocking()


if __name__ == "__main__":
    main()
