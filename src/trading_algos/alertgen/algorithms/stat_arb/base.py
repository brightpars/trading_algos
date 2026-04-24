from __future__ import annotations

from typing import Any, Sequence, cast

from trading_algos.alertgen.algorithms.cross_asset_macro_carry.helpers import (
    MultiLegRow,
    build_multi_leg_output,
    build_multi_leg_rebalance_output,
)
from trading_algos.alertgen.algorithms.stat_arb.helpers import StatArbRow
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.contracts.multi_leg_output import (
    MultiLegOutput,
    MultiLegRebalancePoint,
)


def _signed_leg_weight(weight: float, side: str) -> float:
    if side == "short":
        return -abs(weight)
    if side == "long":
        return abs(weight)
    return 0.0


class BaseStatArbAlertAlgorithm:
    catalog_ref = ""

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        alg_name: str,
        family: str,
        subcategory: str,
        rows: Sequence[StatArbRow],
    ) -> None:
        self.algorithm_key = algorithm_key
        self.symbol = symbol
        self.alg_name = alg_name
        self.family = family
        self.subcategory = subcategory
        self._rows = tuple(rows)
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}

    def minimum_history(self) -> int:
        if not self._rows:
            return 1
        value = self._rows[-1].diagnostics.get(
            "warmup_period",
            self._rows[-1].diagnostics.get("minimum_history", 1),
        )
        return int(cast(int | float | str, value))

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def current_decision(self) -> AlgorithmDecision:
        latest = self._rows[-1] if self._rows else None
        is_active = bool(latest and latest.legs)
        confidence = min(abs(latest.zscore or 0.0) / 3.0, 1.0) if latest else 0.0
        return AlgorithmDecision(
            trend="buy" if is_active else "neutral",
            confidence=confidence,
            buy_signal=is_active,
            sell_signal=False,
            no_signal=not is_active,
            annotations={"alg_name": self.alg_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def portfolio_output(self) -> MultiLegOutput:
        multi_leg_rows: list[MultiLegRow] = []
        for row in self._rows:
            gross_exposure = sum(abs(leg.weight) for leg in row.legs)
            net_exposure = sum(
                _signed_leg_weight(leg.weight, leg.side) for leg in row.legs
            )
            multi_leg_rows.append(
                MultiLegRow(
                    timestamp=row.timestamp,
                    spread_value=row.spread_value,
                    legs=row.legs,
                    diagnostics={
                        **row.diagnostics,
                        "hedge_ratio": row.hedge_ratio,
                        "gross_exposure": gross_exposure,
                        "net_exposure": net_exposure,
                    },
                )
            )
        output = build_multi_leg_output(
            self.algorithm_key,
            multi_leg_rows,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
        )
        rebalances = tuple(
            MultiLegRebalancePoint(
                timestamp=rebalance.timestamp,
                spread_value=rebalance.spread_value,
                legs=rebalance.legs,
                hedge_ratio=float(rebalance.diagnostics.get("hedge_ratio", 1.0)),
                gross_exposure=float(rebalance.diagnostics.get("gross_exposure", 0.0)),
                net_exposure=float(rebalance.diagnostics.get("net_exposure", 0.0)),
                diagnostics=rebalance.diagnostics,
            )
            for rebalance in output.rebalances
        )
        return MultiLegOutput(
            algorithm_key=output.algorithm_key,
            rebalances=rebalances,
            metadata={
                **output.metadata,
                "reporting_mode": "multi_leg",
                "warmup_period": self.minimum_history(),
                "output_target": "multi_leg_positions",
            },
        )

    def normalized_output(self):
        multi_leg_rows: list[MultiLegRow] = []
        for row in self._rows:
            gross_exposure = sum(abs(leg.weight) for leg in row.legs)
            net_exposure = sum(
                _signed_leg_weight(leg.weight, leg.side) for leg in row.legs
            )
            multi_leg_rows.append(
                MultiLegRow(
                    timestamp=row.timestamp,
                    spread_value=row.spread_value,
                    legs=row.legs,
                    diagnostics={
                        **row.diagnostics,
                        "hedge_ratio": row.hedge_ratio,
                        "gross_exposure": gross_exposure,
                        "net_exposure": net_exposure,
                        "zscore": row.zscore,
                    },
                )
            )
        output = build_multi_leg_rebalance_output(
            algorithm_key=self.algorithm_key,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
            rows=multi_leg_rows,
        )
        output.metadata["reporting_mode"] = "multi_leg"
        output.metadata["warmup_period"] = self.minimum_history()
        output.metadata["output_target"] = "multi_leg_positions"
        return output

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        payload = {
            "algorithm_key": self.algorithm_key,
            "data": self.normalized_output().to_dict(),
            "portfolio": self.portfolio_output().to_dict(),
        }
        return [(payload, f"multi_leg_report_{self.algorithm_key}_{self.symbol}")]
