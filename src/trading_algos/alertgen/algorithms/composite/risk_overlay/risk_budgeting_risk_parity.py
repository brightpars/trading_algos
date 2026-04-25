from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.composite.shared_rebalance import (
    CompositeRebalanceRow,
    build_interactive_rebalance_payload,
    build_portfolio_weight_output,
    build_rebalance_alert_output,
    clamp_signed_unit,
    clamp_unit_interval,
    compute_mean,
    compute_volatility,
    extract_sleeve_returns,
    filter_rebalance_rows,
    normalize_weight_map,
)
from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.contracts.portfolio_output import RankedAsset


def evaluate_risk_budget_rows(
    raw_rows: list[dict[str, Any]],
    *,
    rebalance_frequency: str,
    target_gross_exposure: float,
    min_history: int,
) -> tuple[CompositeRebalanceRow, ...]:
    rows: list[CompositeRebalanceRow] = []
    for raw_row in filter_rebalance_rows(
        raw_rows,
        rebalance_frequency=rebalance_frequency,
    ):
        timestamp = str(raw_row.get("ts", raw_row.get("timestamp", ""))).strip()
        sleeve_returns = extract_sleeve_returns(raw_row, label="risk_budgeting")
        stats: list[tuple[str, float, float, float]] = []
        insufficient_history: list[str] = []
        for sleeve, values in sleeve_returns.items():
            if len(values) < min_history:
                insufficient_history.append(sleeve)
                continue
            volatility = compute_volatility(values)
            inverse_risk_weight = 0.0 if volatility <= 0.0 else 1.0 / volatility
            stats.append(
                (sleeve, compute_mean(values), volatility, inverse_risk_weight)
            )
        ordered = sorted(
            stats,
            key=lambda item: (item[2], -item[1], item[0]),
        )
        raw_weights = {
            sleeve: inverse_risk_weight
            for sleeve, _mean_return, _volatility, inverse_risk_weight in ordered
            if inverse_risk_weight > 0.0
        }
        weights = normalize_weight_map(
            raw_weights,
            cap_gross_exposure=target_gross_exposure,
        )
        selected_symbols = tuple(
            symbol for symbol, weight in weights.items() if weight > 0.0
        )
        ranking = tuple(
            RankedAsset(
                symbol=sleeve,
                rank=index,
                score=-volatility,
                weight=weights.get(sleeve, 0.0),
                selected=sleeve in selected_symbols,
                side="long" if sleeve in selected_symbols else "neutral",
            )
            for index, (
                sleeve,
                _mean_return,
                volatility,
                _inverse_risk_weight,
            ) in enumerate(ordered, start=1)
        )
        total_inverse_risk = sum(
            inverse_risk_weight for *_head, inverse_risk_weight in ordered
        )
        risk_contributions = {
            sleeve: (
                0.0
                if total_inverse_risk <= 0.0
                else inverse_risk_weight / total_inverse_risk
            )
            for sleeve, _mean_return, _volatility, inverse_risk_weight in ordered
        }
        selection_reason = "selection_ready"
        if not ordered:
            selection_reason = "warmup_pending"
        diagnostics = {
            "rebalance_frequency": raw_row.get("rebalance_frequency", "monthly"),
            "warmup_ready": bool(ordered),
            "selection_reason": selection_reason,
            "selected_symbols": list(selected_symbols),
            "selected_count": len(selected_symbols),
            "target_gross_exposure": target_gross_exposure,
            "risk_contributions": risk_contributions,
            "insufficient_history_sleeves": tuple(sorted(insufficient_history)),
            "volatility_by_sleeve": {
                sleeve: volatility
                for sleeve, _mean_return, volatility, _inverse_risk_weight in ordered
            },
            "mean_return_by_sleeve": {
                sleeve: mean_return
                for sleeve, mean_return, _volatility, _inverse_risk_weight in ordered
            },
            "top_ranked_symbol": ranking[0].symbol if ranking else None,
            "top_ranked_score": ranking[0].score if ranking else None,
        }
        rows.append(
            CompositeRebalanceRow(
                timestamp=timestamp,
                ranking=ranking,
                selected_symbols=selected_symbols,
                weights=weights,
                diagnostics=diagnostics,
            )
        )
    return tuple(rows)


class RiskBudgetingRiskParityAlertAlgorithm:
    catalog_ref = "combination:5"

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
        self._rows = evaluate_risk_budget_rows(
            list(params["rows"]),
            rebalance_frequency=str(params["rebalance_frequency"]),
            target_gross_exposure=float(params["target_gross_exposure"]),
            min_history=int(params["min_history"]),
        )
        self.latest_predicted_trend = (
            "buy" if self._rows and self._rows[-1].weights else "neutral"
        )
        self.latest_predicted_trend_confidence = (
            clamp_unit_interval(
                sum(abs(weight) for weight in self._rows[-1].weights.values())
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
            subcategory="risk",
            catalog_ref=self.catalog_ref,
            reporting_mode="allocation_trace",
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        return build_rebalance_alert_output(
            algorithm_key=self.algorithm_key,
            family="risk_overlay",
            subcategory="risk",
            catalog_ref=self.catalog_ref,
            reporting_mode="allocation_trace",
            warmup_period=self.minimum_history(),
            rows=self._rows,
            signal_from_row=lambda row: "buy" if row.weights else "neutral",
            score_from_row=lambda row: clamp_signed_unit(sum(row.weights.values())),
            confidence_from_row=lambda row: clamp_unit_interval(
                sum(abs(weight) for weight in row.weights.values())
            ),
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return build_interactive_rebalance_payload(
            algorithm_key=self.algorithm_key,
            symbol=self.symbol,
            output=self.normalized_output(),
            portfolio=self.portfolio_output(),
        )


def build_risk_budgeting_risk_parity_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> RiskBudgetingRiskParityAlertAlgorithm:
    return RiskBudgetingRiskParityAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
