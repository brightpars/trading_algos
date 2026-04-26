from __future__ import annotations

from typing import Any, Sequence

from trading_algos.alertgen.algorithms.cross_asset_macro_carry.helpers import (
    CrossAssetRow,
    MultiLegRow,
    build_cross_asset_portfolio_output,
    build_multi_leg_output,
    build_multi_leg_rebalance_output,
    build_rebalance_output,
)
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)


class CrossAssetRankingAlertAlgorithm:
    catalog_ref = ""

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        alg_name: str,
        family: str,
        subcategory: str,
        rows: Sequence[CrossAssetRow],
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
        self.latest_predicted_trend = "buy" if self._has_selection() else "neutral"
        self.latest_predicted_trend_confidence = self._latest_confidence()

    def _has_selection(self) -> bool:
        return bool(self._rows and self._rows[-1].selected_symbols)

    def _latest_confidence(self) -> float:
        if not self._rows:
            return 0.0
        raw_value = self._rows[-1].diagnostics.get("selection_strength", 0.0)
        return float(raw_value) if isinstance(raw_value, int | float) else 0.0

    def minimum_history(self) -> int:
        return 1

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
        return build_cross_asset_portfolio_output(
            self.algorithm_key,
            self._rows,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
        )

    def normalized_output(self):
        return build_rebalance_output(
            algorithm_key=self.algorithm_key,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
            rows=self._rows,
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        output = self.normalized_output()
        payload = {
            "algorithm_key": self.algorithm_key,
            "data": output.to_dict(),
            "portfolio": self.portfolio_output().to_dict(),
        }
        return [(payload, f"rebalance_report_{self.algorithm_key}_{self.symbol}")]


class CrossAssetMultiLegAlertAlgorithm:
    catalog_ref = ""

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        alg_name: str,
        family: str,
        subcategory: str,
        rows: Sequence[MultiLegRow],
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
        return 1

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
        confidence = 1.0 if is_active else 0.0
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

    def portfolio_output(self):
        return build_multi_leg_output(
            self.algorithm_key,
            self._rows,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
        )

    def normalized_output(self):
        return build_multi_leg_rebalance_output(
            algorithm_key=self.algorithm_key,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
            rows=self._rows,
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        output = self.normalized_output()
        payload = {
            "algorithm_key": self.algorithm_key,
            "data": output.to_dict(),
            "portfolio": self.portfolio_output().to_dict(),
        }
        return [(payload, f"multi_leg_report_{self.algorithm_key}_{self.symbol}")]
