from __future__ import annotations

import argparse
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import mongoengine
from pymongo import MongoClient
from pymongo.database import Database
from trading_servers import CentralServer
from trading_servers import DataServer
from trading_servers import FakeDateTimeServer
from trading_servers.xmlrpc_server import Base_XML_RPC_Server

from trading_algos_dashboard.services.algorithm_runner_service import (
    run_alert_algorithm,
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
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._stop_requested = False
        self._state_lock = threading.Lock()

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
        with self._state_lock:
            self._stop_requested = True
        return 0

    def run_engine_chain(self, obj: Any) -> dict[str, Any]:
        self.reject_if_shutting_down()
        payload = dict(obj or {})
        with self._state_lock:
            self._stop_requested = False

        symbol = str(payload.get("symbol", "")).strip()
        report_base_path = str(payload.get("report_base_path", "")).strip()
        alertgens = payload.get("alertgens") or []
        decmaker = payload.get("decmaker") or {}
        candles = payload.get("candles") or []
        started_at = datetime.now(timezone.utc)
        started_at_iso = started_at.isoformat()

        if not symbol:
            raise ValueError("engine_chain requires symbol")
        if not isinstance(alertgens, list) or len(alertgens) == 0:
            raise ValueError("engine_chain requires at least one alertgen")
        if not isinstance(decmaker, dict):
            raise ValueError("engine_chain requires decmaker")

        child_results: list[dict[str, Any]] = []
        latest_decisions: list[dict[str, Any]] = []
        execution_steps: list[dict[str, Any]] = []
        for alertgen in alertgens:
            with self._state_lock:
                if self._stop_requested:
                    raise RuntimeError("engine_chain stopped before completion")
            result = run_alert_algorithm(
                sensor_config=dict(alertgen),
                report_base_path=report_base_path,
                candles=list(candles),
            )
            child_results.append(result)
            latest_decision = dict(result.get("latest_decision") or {})
            latest_decision["alg_key"] = result.get("alg_key")
            latest_decisions.append(latest_decision)
            execution_steps.extend(
                [dict(step) for step in result.get("execution_steps") or []]
            )

        decmaker_result = self._build_decmaker_result(
            symbol=symbol,
            decmaker=dict(decmaker),
            latest_decisions=latest_decisions,
        )
        finished_at = datetime.now(timezone.utc)
        execution_steps.append(
            {
                "step": "run_engine_chain",
                "label": "Run engine chain",
                "started_at": started_at_iso,
                "finished_at": finished_at.isoformat(),
                "duration_seconds": (finished_at - started_at).total_seconds(),
                "metadata": {
                    "symbol": symbol,
                    "alertgen_count": len(child_results),
                    "decmaker_key": decmaker_result["decmaker_key"],
                },
            }
        )
        return {
            "input_kind": "engine_chain",
            "symbol": symbol,
            "alg_name": f"Engine chain for {symbol}",
            "execution_steps": execution_steps,
            "signal_summary": {
                "alertgen_count": len(child_results),
                "buy_signal_count": sum(
                    1 for item in latest_decisions if bool(item.get("buy_signal"))
                ),
                "sell_signal_count": sum(
                    1 for item in latest_decisions if bool(item.get("sell_signal"))
                ),
            },
            "latest_decision": decmaker_result["latest_decision"],
            "report": {
                "report_version": "1.0",
                "schema_version": "1.0",
                "algorithm_summary": {
                    "algorithm_name": f"Engine chain for {symbol}",
                    "algorithm_key": "engine_chain",
                },
                "summary_cards": [
                    {
                        "label": "Alertgens",
                        "value": str(len(child_results)),
                        "metric_key": "alertgen_count",
                    },
                    {
                        "label": "Decision",
                        "value": decmaker_result["latest_decision"]["trend"],
                        "metric_key": "final_decision",
                    },
                ],
                "evaluation_summary": {
                    "headline_metrics": decmaker_result,
                },
                "charts": [],
                "tables": [],
                "analysis_blocks": [],
                "diagnostics": {
                    "alertgen_results": [
                        {
                            "alg_key": result.get("alg_key"),
                            "signal_summary": result.get("signal_summary"),
                            "latest_decision": result.get("latest_decision"),
                        }
                        for result in child_results
                    ],
                    "decmaker": decmaker_result,
                },
            },
            "node_results": [
                {
                    "node_id": f"alertgen_{index}",
                    "node_type": "alertgen",
                    "node_name": result.get("alg_name") or result.get("alg_key"),
                }
                for index, result in enumerate(child_results, start=1)
            ]
            + [
                {
                    "node_id": "decmaker_1",
                    "node_type": "decmaker",
                    "node_name": decmaker_result["decmaker_key"],
                }
            ],
        }

    def stop_engine_chain(self) -> int:
        self.reject_if_shutting_down()
        with self._state_lock:
            self._stop_requested = True
        return 0

    def _build_decmaker_result(
        self,
        *,
        symbol: str,
        decmaker: dict[str, Any],
        latest_decisions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        decmaker_key = str(decmaker.get("decmaker_key", "alg1"))
        decmaker_param = dict(decmaker.get("decmaker_param") or {})
        buy_threshold = float(decmaker_param.get("confidence_threshold_buy", 0.6))
        sell_threshold = float(decmaker_param.get("confidence_threshold_sell", 0.6))
        buy_candidates = [
            item
            for item in latest_decisions
            if bool(item.get("buy_signal"))
            and float(item.get("confidence", 0.0) or 0.0) >= buy_threshold
        ]
        sell_candidates = [
            item
            for item in latest_decisions
            if bool(item.get("sell_signal"))
            and float(item.get("confidence", 0.0) or 0.0) >= sell_threshold
        ]
        trend = "no_signal"
        if len(buy_candidates) > len(sell_candidates):
            trend = "buy"
        elif len(sell_candidates) > len(buy_candidates):
            trend = "sell"
        confidence = 0.0
        if trend == "buy" and buy_candidates:
            confidence = max(
                float(item.get("confidence", 0.0) or 0.0) for item in buy_candidates
            )
        elif trend == "sell" and sell_candidates:
            confidence = max(
                float(item.get("confidence", 0.0) or 0.0) for item in sell_candidates
            )
        return {
            "symbol": symbol,
            "decmaker_key": decmaker_key,
            "decmaker_param": decmaker_param,
            "buy_candidate_count": len(buy_candidates),
            "sell_candidate_count": len(sell_candidates),
            "latest_decision": {
                "trend": trend,
                "confidence": confidence,
                "buy_signal": trend == "buy",
                "sell_signal": trend == "sell",
                "buy_range_signal": False,
                "sell_range_signal": False,
                "no_signal": trend == "no_signal",
                "annotations": {
                    "buy_candidate_count": len(buy_candidates),
                    "sell_candidate_count": len(sell_candidates),
                    "decmaker_key": decmaker_key,
                },
            },
        }

    def register_all_functions(self) -> None:
        self.server.register_function(self.start_decision_maker)
        self.server.register_function(self.run_alertgen_and_sensors)
        self.server.register_function(self.run_all_engines)
        self.server.register_function(self.stop_all_engines)
        self.server.register_function(self.run_engine_chain)
        self.server.register_function(self.stop_engine_chain)


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
