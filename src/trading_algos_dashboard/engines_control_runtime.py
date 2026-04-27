from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
import socket
from time import perf_counter
from typing import Any
from xmlrpc.client import ServerProxy

from trading_servers.xmlrpc_server import Base_XML_RPC_Server

from trading_algos.decmaker.factory import create_decmaker_algorithm
from trading_algos_dashboard.services.algorithm_runner_service import (
    run_alert_algorithm,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class _DecisionMakerContainer:
    latest_buy_alert: dict[str, Any] | None
    latest_sell_alert: dict[str, Any] | None

    def mark_alert_as_processed(self, alert_id: str) -> None:
        return None

    def how_much_usd_available_for_buying(self) -> float:
        return 1.0

    def how_many_of_asset_are_available_to_sell(self, symbol: str) -> int:
        return 1 if symbol else 0

    def submit_buy_operation(
        self,
        *,
        alert: dict[str, Any],
        no: int,
        initiationReason: str,
    ) -> None:
        return None

    def submit_sell_operation(
        self,
        *,
        alert: dict[str, Any],
        no: int,
        initiationReason: str,
    ) -> None:
        return None


@dataclass
class _RuntimeState:
    alertgen_infos: list[dict[str, Any]]
    decision_maker_info: dict[str, Any] | None
    alertgen_reports: list[dict[str, Any]]
    decision_maker_report: dict[str, Any]
    alertgen_stop_reports: list[dict[str, Any]] | None
    decision_maker_stop_report: dict[str, Any] | None
    alertgens_running: bool
    decision_maker_running: bool
    alertgen_stop_complete: bool
    decision_maker_stop_complete: bool


def _empty_runtime_state() -> _RuntimeState:
    return _RuntimeState(
        alertgen_infos=[],
        decision_maker_info=None,
        alertgen_reports=[],
        decision_maker_report={},
        alertgen_stop_reports=[],
        decision_maker_stop_report={},
        alertgens_running=False,
        decision_maker_running=False,
        alertgen_stop_complete=True,
        decision_maker_stop_complete=True,
    )


class EnginesControlRuntimeServer(Base_XML_RPC_Server):
    def __init__(
        self,
        *,
        user_id: int,
        ip: str,
        port: int,
        sever_name: str,
        log_requests_to_terminal: bool,
    ) -> None:
        super().__init__(
            user_id=user_id,
            ip=ip,
            port=port,
            server_name=sever_name,
            log_requests_to_terminal=log_requests_to_terminal,
        )
        self._stop_requested = False
        self._state = _empty_runtime_state()

    def register_all_functions(self) -> None:
        self.server.register_function(
            self.run_alertgen_and_sensors_rpc, "run_alertgen_and_sensors"
        )
        self.server.register_function(self.get_all_alertgen_info)
        self.server.register_function(self.stop_all_alertgen_instances)
        self.server.register_function(
            self.start_decision_maker_rpc, "start_decision_maker"
        )
        self.server.register_function(self.get_decision_maker_info)
        self.server.register_function(self.stop_decision_maker_instance)
        self.server.register_function(self.is_decision_maker_stop_complete)
        self.server.register_function(self.get_decision_maker_stop_report)
        self.server.register_function(self.get_all_engines_reports)
        self.server.register_function(self.check_connections)
        self.server.register_function(self.run_all_engines)
        self.server.register_function(self.pause_all_engines)
        self.server.register_function(self.is_alertgen_stop_complete)
        self.server.register_function(self.get_alertgen_stop_reports)
        self.server.register_function(self.run_engine_chain_rpc, "run_engine_chain")
        self.server.register_function(self.stop_engine_chain)

    def stop_engine_chain(self) -> int:
        self._stop_requested = True
        return 0

    def run_engine_chain(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.reject_if_shutting_down()
        self._stop_requested = False
        result = run_engine_chain_payload(payload)
        self._state.alertgen_reports = [
            dict(item)
            for item in list(
                result.get("report", {})
                .get("diagnostics", {})
                .get("alertgen_results", [])
            )
            if isinstance(item, dict)
        ]
        self._state.alertgen_infos = _alertgen_infos_from_results(
            self.server_name,
            self._state.alertgen_reports,
        )
        self._state.decision_maker_info = _build_decision_maker_info(
            self.server_name,
            dict(payload.get("decmaker") or {}),
        )
        self._state.decision_maker_report = {
            "latest_decision": dict(result.get("latest_decision") or {}),
            "signal_summary": dict(result.get("signal_summary") or {}),
        }
        self._state.alertgens_running = True
        self._state.decision_maker_running = True
        self._state.alertgen_stop_complete = False
        self._state.decision_maker_stop_complete = False
        self._state.alertgen_stop_reports = []
        self._state.decision_maker_stop_report = {}
        return result

    def run_engine_chain_rpc(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Engine chain payload must be a dict")
        return self.run_engine_chain(payload)

    def run_alertgen_and_sensors_rpc(self, payload: Any) -> int | str:
        if not isinstance(payload, dict):
            raise ValueError("Alertgen payload must be a dict")
        return self.run_alertgen_and_sensors(payload)

    def run_alertgen_and_sensors(self, payload: dict[str, Any]) -> int | str:
        self.reject_if_shutting_down()
        if self._state.alertgens_running:
            return "already_run_is_called"
        execution_id = str(payload.get("execution_id", "runtime"))
        raw_configs = payload.get("alertgen_config_list")
        if not isinstance(raw_configs, list):
            raise ValueError("alertgen_config_list must be a list")
        infos: list[dict[str, Any]] = []
        for index, item in enumerate(raw_configs, start=1):
            if not isinstance(item, dict):
                continue
            if not bool(item.get("enable", True)):
                continue
            engine_config = item.get("engine_config") or {}
            if not isinstance(engine_config, dict):
                raise ValueError("engine_config must be a dict")
            sensors = item.get("sensors") or [
                {"name": f"sensor_{index}", "sensor_config": {}}
            ]
            if not isinstance(sensors, list):
                raise ValueError("sensors must be a list")
            for sensor_index, sensor in enumerate(sensors, start=1):
                if not isinstance(sensor, dict):
                    continue
                if not bool(sensor.get("enable", True)):
                    continue
                sensor_name = str(sensor.get("name") or f"sensor_{sensor_index}")
                infos.append(
                    {
                        "server": self.server_name,
                        "name": f"{item.get('name', 'alertgen')}:{sensor_name}",
                        "type": str(engine_config.get("type", "alertgen")),
                        "config": {
                            "engine_config": dict(engine_config),
                            "sensor_name": sensor_name,
                            "sensor_config": dict(sensor.get("sensor_config") or {}),
                            "execution_id": execution_id,
                        },
                    }
                )
        self._state.alertgen_infos = infos
        self._state.alertgens_running = bool(infos)
        self._state.alertgen_stop_complete = not bool(infos)
        self._state.alertgen_stop_reports = []
        self._state.alertgen_reports = []
        return 0

    def get_all_alertgen_info(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._state.alertgen_infos]

    def stop_all_alertgen_instances(self) -> list[dict[str, Any]]:
        reports = [
            {
                "name": str(item.get("name", "alertgen")),
                "stopped_at": _utc_now().isoformat(),
            }
            for item in self._state.alertgen_infos
        ]
        self._state.alertgen_stop_reports = reports
        self._state.alertgen_infos = []
        self._state.alertgens_running = False
        self._state.alertgen_stop_complete = True
        return list(reports)

    def start_decision_maker_rpc(self, payload: Any) -> int | str:
        if not isinstance(payload, dict):
            raise ValueError("Decision maker payload must be a dict")
        return self.start_decision_maker(payload)

    def start_decision_maker(self, payload: dict[str, Any]) -> int | str:
        self.reject_if_shutting_down()
        if self._state.decision_maker_running:
            return "already_decision_maker_is_up"
        config = payload.get("config")
        if not isinstance(config, dict):
            raise ValueError("config must be a dict")
        if not bool(config.get("enable", False)):
            self._state.decision_maker_info = None
            self._state.decision_maker_running = False
            self._state.decision_maker_stop_complete = True
            self._state.decision_maker_stop_report = {}
            return 0
        engine_config = config.get("engine_config")
        if not isinstance(engine_config, dict):
            raise ValueError("engine_config must be a dict")
        self._state.decision_maker_info = {
            "server": self.server_name,
            "name": str(config.get("name", "decision_maker")),
            "type": str(engine_config.get("type", "dec1")),
            "config": {"engine_config": dict(engine_config)},
        }
        self._state.decision_maker_running = True
        self._state.decision_maker_stop_complete = False
        self._state.decision_maker_stop_report = {}
        return 0

    def get_decision_maker_info(self) -> dict[str, Any]:
        return (
            dict(self._state.decision_maker_info)
            if isinstance(self._state.decision_maker_info, dict)
            else {}
        )

    def stop_decision_maker_instance(self) -> dict[str, Any]:
        report = {
            "stopped_at": _utc_now().isoformat(),
            "name": str(
                (self._state.decision_maker_info or {}).get("name", "decision_maker")
            ),
        }
        self._state.decision_maker_stop_report = report
        self._state.decision_maker_info = None
        self._state.decision_maker_running = False
        self._state.decision_maker_stop_complete = True
        return dict(report)

    def is_decision_maker_stop_complete(self) -> bool:
        return bool(self._state.decision_maker_stop_complete)

    def get_decision_maker_stop_report(self) -> dict[str, Any] | None:
        report = self._state.decision_maker_stop_report
        return None if report is None else dict(report)

    def get_all_engines_reports(self) -> dict[str, Any]:
        return {
            "decisionmaker_report_dict": dict(self._state.decision_maker_report),
            "alertgen_report_dict_list": [
                dict(item)
                for item in self._state.alertgen_reports
                if isinstance(item, dict)
            ],
        }

    def check_connections(self) -> list[dict[str, str]]:
        return [
            {f"{name}({host}:{port})": _service_state(host, port)}
            for name, host, port in _connection_targets()
        ]

    def run_all_engines(self) -> int:
        self._state.alertgens_running = bool(self._state.alertgen_infos) or bool(
            self._state.alertgen_reports
        )
        self._state.decision_maker_running = self._state.decision_maker_info is not None
        return 0

    def pause_all_engines(self) -> int:
        self._state.alertgens_running = False
        self._state.decision_maker_running = False
        return 0

    def is_alertgen_stop_complete(self) -> bool:
        return bool(self._state.alertgen_stop_complete)

    def get_alertgen_stop_reports(self) -> list[dict[str, Any]] | None:
        reports = self._state.alertgen_stop_reports
        if reports is None:
            return None
        return [dict(item) for item in reports]


def run_engine_chain_payload(payload: dict[str, Any]) -> dict[str, Any]:
    started_at = _utc_now()
    started_at_perf = perf_counter()
    symbol = str(payload["symbol"])
    report_base_path = str(payload["report_base_path"])
    candles = list(payload["candles"])
    alertgen_payloads = [dict(item) for item in list(payload["alertgens"])]
    decmaker_payload = dict(payload["decmaker"])

    alertgen_results = [
        run_alert_algorithm(
            sensor_config=dict(alertgen_payload),
            report_base_path=report_base_path,
            candles=candles,
        )
        for alertgen_payload in alertgen_payloads
    ]

    latest_decision = _combine_latest_decision(
        symbol=symbol,
        alertgen_results=alertgen_results,
        decmaker_payload=decmaker_payload,
    )
    signal_summary = _build_signal_summary(alertgen_results)
    finished_at = _utc_now()
    duration_seconds = perf_counter() - started_at_perf

    return {
        "input_kind": "engine_chain",
        "alg_name": f"Engine chain for {symbol}",
        "execution_steps": [
            {
                "step": "run_engine_chain",
                "label": "Run engine chain",
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_seconds": duration_seconds,
                "metadata": {
                    "symbol": symbol,
                    "alertgen_count": len(alertgen_results),
                    "candle_count": len(candles),
                    "decmaker_key": str(decmaker_payload.get("decmaker_key", "")),
                },
            }
        ],
        "latest_decision": latest_decision,
        "signal_summary": signal_summary,
        "report": {
            "report_version": "1.0",
            "schema_version": "1.0",
            "algorithm_summary": {
                "algorithm_name": f"Engine chain for {symbol}",
                "algorithm_key": "engine_chain",
                "family": "engine_chain",
                "runtime_kind": "engine_chain",
                "parameter_values": {
                    "decmaker": decmaker_payload,
                    "alertgens": [
                        {
                            "alg_key": result.get("alg_key"),
                            "alg_param": result.get("alg_param"),
                        }
                        for result in alertgen_results
                    ],
                },
            },
            "summary_cards": [],
            "evaluation_summary": {"headline_metrics": {}},
            "charts": [],
            "diagnostics": {
                "alertgen_results": alertgen_results,
            },
        },
    }


def _build_signal_summary(alertgen_results: list[dict[str, Any]]) -> dict[str, Any]:
    buy_count = 0
    sell_count = 0
    total_rows = 0
    for result in alertgen_results:
        summary = result.get("signal_summary")
        if not isinstance(summary, dict):
            continue
        buy_count += int(summary.get("buy_count", 0) or 0)
        sell_count += int(summary.get("sell_count", 0) or 0)
        total_rows = max(total_rows, int(summary.get("total_rows", 0) or 0))
    return {
        "alertgen_count": len(alertgen_results),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "total_rows": total_rows,
    }


def _combine_latest_decision(
    *,
    symbol: str,
    alertgen_results: list[dict[str, Any]],
    decmaker_payload: dict[str, Any],
) -> dict[str, Any]:
    alerts = _build_decmaker_alerts(symbol=symbol, alertgen_results=alertgen_results)
    container = _DecisionMakerContainer(
        latest_buy_alert=next(
            (alert for alert in reversed(alerts) if alert["alertType"] == "strong buy"),
            None,
        ),
        latest_sell_alert=next(
            (
                alert
                for alert in reversed(alerts)
                if alert["alertType"] == "strong sell"
            ),
            None,
        ),
    )
    decision_maker = create_decmaker_algorithm(
        container_obj=container,
        engine_config=dict(decmaker_payload.get("decmaker_param") or {}),
    )
    decision_maker.process_alerts_list(alerts)

    buy_confidence = max(
        (
            float(result["latest_decision"].get("confidence", 0.0) or 0.0)
            for result in alertgen_results
            if isinstance(result.get("latest_decision"), dict)
            and bool(result["latest_decision"].get("buy_signal"))
        ),
        default=0.0,
    )
    sell_confidence = max(
        (
            float(result["latest_decision"].get("confidence", 0.0) or 0.0)
            for result in alertgen_results
            if isinstance(result.get("latest_decision"), dict)
            and bool(result["latest_decision"].get("sell_signal"))
        ),
        default=0.0,
    )
    if buy_confidence > sell_confidence:
        return {
            "trend": "buy",
            "confidence": buy_confidence,
            "buy_signal": True,
            "sell_signal": False,
            "buy_range_signal": False,
            "sell_range_signal": False,
            "no_signal": False,
            "annotations": {"symbol": symbol},
        }
    if sell_confidence > buy_confidence:
        return {
            "trend": "sell",
            "confidence": sell_confidence,
            "buy_signal": False,
            "sell_signal": True,
            "buy_range_signal": False,
            "sell_range_signal": False,
            "no_signal": False,
            "annotations": {"symbol": symbol},
        }
    return {
        "trend": "neutral",
        "confidence": 0.0,
        "buy_signal": False,
        "sell_signal": False,
        "buy_range_signal": False,
        "sell_range_signal": False,
        "no_signal": True,
        "annotations": {"symbol": symbol},
    }


def _build_decmaker_alerts(
    *, symbol: str, alertgen_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for index, result in enumerate(alertgen_results, start=1):
        latest_decision = result.get("latest_decision")
        if not isinstance(latest_decision, dict):
            continue
        confidence = float(latest_decision.get("confidence", 0.0) or 0.0)
        if latest_decision.get("buy_signal"):
            alerts.append(
                {
                    "alertID": f"buy-{index}",
                    "alertType": "strong buy",
                    "alertDetails": {
                        "confidence": confidence,
                        "price": 1.0,
                        "symbol": symbol,
                    },
                }
            )
        if latest_decision.get("sell_signal"):
            alerts.append(
                {
                    "alertID": f"sell-{index}",
                    "alertType": "strong sell",
                    "alertDetails": {
                        "confidence": confidence,
                        "price": 1.0,
                        "symbol": symbol,
                    },
                }
            )
    return alerts


def _alertgen_infos_from_results(
    server_name: str, alertgen_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    infos: list[dict[str, Any]] = []
    for index, result in enumerate(alertgen_results, start=1):
        infos.append(
            {
                "server": server_name,
                "name": str(result.get("alg_name") or f"alertgen_{index}"),
                "type": "alertgen",
                "config": {
                    "engine_config": {
                        "alg_key": result.get("alg_key"),
                        "alg_param": result.get("alg_param"),
                    },
                    "sensor_name": f"sensor_{index}",
                    "sensor_config": {},
                },
            }
        )
    return infos


def _build_decision_maker_info(
    server_name: str, decmaker_payload: dict[str, Any]
) -> dict[str, Any]:
    return {
        "server": server_name,
        "name": "decision_maker",
        "type": str(decmaker_payload.get("decmaker_key", "dec1") or "dec1"),
        "config": {"engine_config": dict(decmaker_payload.get("decmaker_param") or {})},
    }


def _connection_targets() -> list[tuple[str, str, int]]:
    return [
        (
            "central",
            os.environ.get("TRADING_ALGOS_DASHBOARD_CENTRAL_HOST", "127.0.0.1").strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_CENTRAL_PORT", "6000")),
        ),
        (
            "fake_datetime",
            os.environ.get(
                "TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_HOST", "127.0.0.1"
            ).strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_PORT", "7100")),
        ),
        (
            "data",
            os.environ.get("TRADING_ALGOS_DASHBOARD_DATA_HOST", "127.0.0.1").strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_DATA_PORT", "6010")),
        ),
        (
            "broker",
            os.environ.get("TRADING_ALGOS_DASHBOARD_BROKER_HOST", "127.0.0.1").strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_BROKER_PORT", "7101")),
        ),
    ]


def _service_state(host: str, port: int) -> str:
    if _xmlrpc_ping(host, port):
        return "up"
    if _tcp_port_open(host, port):
        return "up"
    return "down"


def _xmlrpc_ping(host: str, port: int) -> bool:
    try:
        proxy = ServerProxy(f"http://{host}:{port}", allow_none=True)
        result = proxy.ping()
        return result == "pong"
    except Exception:
        return False


def _tcp_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False
