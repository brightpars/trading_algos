from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any

import mongoengine  # type: ignore[import-untyped]
from pymongo import MongoClient
from pymongo import ReturnDocument
from pymongo.database import Database
from trading_servers import CentralServer
from trading_servers import DataServer
from trading_servers import FakeDateTimeServer
from trading_servers.xmlrpc_server import Base_XML_RPC_Server

from trading_algos_dashboard.engines_control_runtime import EnginesControlRuntimeServer


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
        return EnginesControlRuntimeServer(
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
