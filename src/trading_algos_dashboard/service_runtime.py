from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any
from typing import Callable

import mongoengine  # type: ignore[import-untyped]
from pymongo import MongoClient
from pymongo import ReturnDocument
from pymongo.database import Database
from trading_servers.xmlrpc_server import Base_XML_RPC_Server

from trading_algos_dashboard.trading_servers_integration import (
    TradingServerRuntimeRequest,
)
from trading_algos_dashboard.trading_servers_integration import build_central_server
from trading_algos_dashboard.trading_servers_integration import build_data_server
from trading_algos_dashboard.trading_servers_integration import (
    build_engines_control_server,
)
from trading_algos_dashboard.trading_servers_integration import (
    build_fake_datetime_server,
)


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
        self._counter_collection = self._db["counters"]
        self._counter_specs: dict[str, tuple[str, str]] = {
            "alert_id": ("alerts", "alertID"),
            "asset_id": ("assets", "assetID"),
            "operation_id": ("operations", "operationID"),
            "execution_id": ("executions", "executionID"),
        }

    def get_counter_seed_value(self, counter_name: str) -> int:
        collection_name, field_name = self._counter_specs[counter_name]
        latest = self._db[collection_name].find_one(
            sort=[(field_name, -1)],
            projection={field_name: True},
        )
        if latest is None:
            return 0
        return int(latest.get(field_name, 0))

    def get_next_counter_value(self, counter_name: str, seed_value: int) -> int:
        result = self._counter_collection.find_one_and_update(
            {"_id": counter_name},
            [{"$set": {"seq": {"$add": [{"$ifNull": ["$seq", int(seed_value)]}, 1]}}}],
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if result is None or "seq" not in result:
            raise RuntimeError(
                f"counter update returned no sequence for counter={counter_name}"
            )
        return int(result["seq"])


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


def _runtime_request(config: ServiceRuntimeConfig) -> TradingServerRuntimeRequest:
    return TradingServerRuntimeRequest(
        name=config.name,
        host=config.host,
        port=config.port,
        user_id=config.user_id,
    )


def _build_central_server(config: ServiceRuntimeConfig) -> Base_XML_RPC_Server:
    mongo_uri, mongo_db_name = _mongo_runtime_settings()
    return build_central_server(
        _runtime_request(config),
        counter_repository=MongoCounterRepository(
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
        ),
    )


def _build_data_server(config: ServiceRuntimeConfig) -> Base_XML_RPC_Server:
    _connect_data_runtime_storage()
    return build_data_server(_runtime_request(config))


def _build_fake_datetime_server(config: ServiceRuntimeConfig) -> Base_XML_RPC_Server:
    return build_fake_datetime_server(_runtime_request(config))


def _build_engines_control_server(config: ServiceRuntimeConfig) -> Base_XML_RPC_Server:
    return build_engines_control_server(_runtime_request(config))


ServerBuilder = Callable[[ServiceRuntimeConfig], Base_XML_RPC_Server]


_SERVER_BUILDERS: dict[str, ServerBuilder] = {
    "central": _build_central_server,
    "data": _build_data_server,
    "fake_datetime": _build_fake_datetime_server,
    "engines_control": _build_engines_control_server,
}


def _build_server(config: ServiceRuntimeConfig) -> Base_XML_RPC_Server:
    builder = _SERVER_BUILDERS.get(config.name)
    if builder is None:
        raise ValueError(f"Unsupported service runtime: {config.name}")
    return builder(config)


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
