from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from trading_servers import CentralServer
from trading_servers import DataServer
from trading_servers import FakeDateTimeServer
from trading_servers.xmlrpc_server import Base_XML_RPC_Server

from trading_algos_dashboard.services.engines_control_runtime_service import (
    EnginesControlRuntimeService,
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


class DashboardEnginesControlServer(Base_XML_RPC_Server):
    def __init__(
        self,
        *args: Any,
        runtime_service: EnginesControlRuntimeService | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._runtime_service = runtime_service or EnginesControlRuntimeService()

    def start_decision_maker(self, _obj: Any) -> int:
        self.reject_if_shutting_down()
        return 0

    def run_alertgen_and_sensors(self, _obj: Any) -> int:
        self.reject_if_shutting_down()
        return 0

    def run_all_engines(self) -> int:
        self.reject_if_shutting_down()
        return 0

    def stop_all_engines(self) -> int:
        self.reject_if_shutting_down()
        return 0

    def run_backtrace(self, request: Any) -> dict[str, Any]:
        self.reject_if_shutting_down()
        result = self._runtime_service.run_backtrace(request)
        return dict(result)

    def register_all_functions(self) -> None:
        self.server.register_function(self.start_decision_maker)
        self.server.register_function(self.run_alertgen_and_sensors)
        self.server.register_function(self.run_all_engines)
        self.server.register_function(self.stop_all_engines)
        self.server.register_function(self.run_backtrace)


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
        return DashboardEnginesControlServer(
            user_id=config.user_id,
            ip=config.host,
            port=config.port,
            server_name=config.name,
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
