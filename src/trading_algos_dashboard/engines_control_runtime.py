from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

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

    def register_all_functions(self) -> None:
        self.server.register_function(self.run_engine_chain_rpc, "run_engine_chain")
        self.server.register_function(self.stop_engine_chain)

    def stop_engine_chain(self) -> int:
        self._stop_requested = True
        return 0

    def run_engine_chain(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.reject_if_shutting_down()
        self._stop_requested = False
        return run_engine_chain_payload(payload)

    def run_engine_chain_rpc(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Engine chain payload must be a dict")
        return self.run_engine_chain(payload)


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
