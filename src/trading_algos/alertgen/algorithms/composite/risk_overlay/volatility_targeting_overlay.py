from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.composite.shared_rebalance import (
    CompositeRebalanceRow,
    build_interactive_rebalance_payload,
    build_portfolio_weight_output,
    build_rebalance_alert_output,
    clamp_signed_unit,
    clamp_unit_interval,
    coerce_float,
    compute_volatility,
    filter_rebalance_rows,
    normalize_weight_map,
)
from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.contracts.portfolio_output import RankedAsset


def _extract_portfolio_returns(raw_row: dict[str, Any]) -> list[float]:
    values = raw_row.get("portfolio_returns", raw_row.get("returns", []))
    if not isinstance(values, list):
        raise ValueError("volatility_targeting: portfolio_returns must be a list")
    return [
        item for item in (coerce_float(value) for value in values) if item is not None
    ]


def evaluate_volatility_target_rows(
    raw_rows: list[dict[str, Any]],
    *,
    target_volatility: float,
    base_weight: float,
    min_history: int,
    max_leverage: float,
    min_leverage: float,
) -> tuple[CompositeRebalanceRow, ...]:
    rows: list[CompositeRebalanceRow] = []
    for raw_row in filter_rebalance_rows(
        raw_rows,
        rebalance_frequency=str(raw_rows[0].get("rebalance_frequency", "all"))
        if raw_rows
        else "all",
    ):
        timestamp = str(raw_row.get("ts", raw_row.get("timestamp", ""))).strip()
        returns = _extract_portfolio_returns(raw_row)
        warmup_ready = len(returns) >= min_history
        realized_vol = compute_volatility(returns) if warmup_ready else 0.0
        if warmup_ready and realized_vol > 0.0:
            leverage = target_volatility / realized_vol
        else:
            leverage = 0.0
        leverage = (
            max(min_leverage, min(max_leverage, leverage)) if warmup_ready else 0.0
        )
        raw_weight = base_weight * leverage if warmup_ready else 0.0
        weights = normalize_weight_map(
            {"portfolio": raw_weight}, cap_gross_exposure=1.0
        )
        weight = weights.get("portfolio", 0.0)
        ranking = (
            RankedAsset(
                symbol="portfolio",
                rank=1,
                score=leverage,
                weight=weight,
                selected=weight != 0.0,
                side="long" if weight > 0.0 else "neutral",
            ),
        )
        selected_symbols = ("portfolio",) if weight != 0.0 else ()
        selection_reason = "selection_ready" if warmup_ready else "warmup_pending"
        diagnostics = {
            "target_volatility": target_volatility,
            "base_weight": base_weight,
            "realized_volatility": realized_vol,
            "applied_leverage": leverage,
            "warmup_ready": warmup_ready,
            "selection_reason": selection_reason,
            "selected_symbols": list(selected_symbols),
            "selected_count": len(selected_symbols),
            "top_ranked_symbol": "portfolio" if selected_symbols else None,
            "top_ranked_score": leverage if selected_symbols else None,
        }
        rows.append(
            CompositeRebalanceRow(
                timestamp=timestamp,
                ranking=ranking if warmup_ready else (),
                selected_symbols=selected_symbols,
                weights=weights,
                diagnostics=diagnostics,
            )
        )
    return tuple(rows)


class VolatilityTargetingOverlayAlertAlgorithm:
    catalog_ref = "combination:6"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.params = params
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self._rows = evaluate_volatility_target_rows(
            list(params["rows"]),
            target_volatility=float(params["target_volatility"]),
            base_weight=float(params["base_weight"]),
            min_history=int(params["min_history"]),
            max_leverage=float(params["max_leverage"]),
            min_leverage=float(params["min_leverage"]),
        )
        self.latest_predicted_trend = (
            "buy" if self._rows and self._rows[-1].weights else "neutral"
        )
        self.latest_predicted_trend_confidence = (
            clamp_unit_interval(
                abs(next(iter(self._rows[-1].weights.values())))
                if self._rows[-1].weights
                else 0.0
            )
            if self._rows
            else 0.0
        )

    def minimum_history(self) -> int:
        return int(self.params["min_history"])

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == "buy",
            sell_signal=False,
            no_signal=self.latest_predicted_trend != "buy",
            annotations={"alg_name": self.alg_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def portfolio_output(self):
        return build_portfolio_weight_output(
            self.algorithm_key,
            self._rows,
            family="risk_overlay",
            subcategory="volatility",
            catalog_ref=self.catalog_ref,
            reporting_mode="allocation_trace",
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        return build_rebalance_alert_output(
            algorithm_key=self.algorithm_key,
            family="risk_overlay",
            subcategory="volatility",
            catalog_ref=self.catalog_ref,
            reporting_mode="allocation_trace",
            warmup_period=self.minimum_history(),
            rows=self._rows,
            signal_from_row=lambda row: "buy" if row.weights else "neutral",
            score_from_row=lambda row: clamp_signed_unit(
                next(iter(row.weights.values())) if row.weights else 0.0
            ),
            confidence_from_row=lambda row: clamp_unit_interval(
                abs(next(iter(row.weights.values())) if row.weights else 0.0)
            ),
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return build_interactive_rebalance_payload(
            algorithm_key=self.algorithm_key,
            symbol=self.symbol,
            output=self.normalized_output(),
            portfolio=self.portfolio_output(),
        )


def build_volatility_targeting_overlay_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> VolatilityTargetingOverlayAlertAlgorithm:
    return VolatilityTargetingOverlayAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
