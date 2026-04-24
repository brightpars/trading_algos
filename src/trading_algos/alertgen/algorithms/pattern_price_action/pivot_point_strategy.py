from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    classic_pivot_levels,
    nearest_level,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class PivotPointStrategyAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:72"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        pivot_lookback: int = 3,
        level_tolerance: float = 0.4,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.pivot_lookback = pivot_lookback
        self.level_tolerance = float(level_tolerance)
        super().__init__(
            f"pivot_point_strategy_lookback={pivot_lookback}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.pivot_lookback + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "pivot_lookback": self.pivot_lookback,
            "level_tolerance": self.level_tolerance,
            "pattern_type": "pivot_point",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "pivot_level": self.latest_data_modifiable.get("pivot_level"),
            "pivot_level_name": self.latest_data_modifiable.get("pivot_level_name"),
            "pivot_distance": self.latest_data_modifiable.get("pivot_distance"),
            "level_supportive": self.latest_data_modifiable.get("level_supportive"),
        }

    def _calculate_state(self) -> PatternSignalState:
        if len(self.data_list) < self.minimum_history():
            return PatternSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.level_tolerance,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        lookback = self.data_list[-self.pivot_lookback - 1 : -1]
        high_value = max(float(item["High"]) for item in lookback)
        low_value = min(float(item["Low"]) for item in lookback)
        close_value = float(lookback[-1]["Close"])
        levels = classic_pivot_levels(high_value, low_value, close_value)
        latest = self.data_list[-1]
        latest_close = float(latest["Close"])
        nearest = nearest_level(latest_close, levels.items())
        assert nearest is not None
        level_name, level_value = nearest
        pivot_distance = latest_close - level_value
        level_supportive = (
            (level_name.startswith("support") or level_name == "pivot")
            and pivot_distance >= 0.0
            and abs(pivot_distance) <= self.level_tolerance
        )
        self.latest_data_modifiable["pivot_level"] = level_value
        self.latest_data_modifiable["pivot_level_name"] = level_name
        self.latest_data_modifiable["pivot_distance"] = pivot_distance
        self.latest_data_modifiable["level_supportive"] = level_supportive
        self.latest_data_modifiable["pivot"] = levels["pivot"]
        self.latest_data_modifiable["support_1"] = levels["support_1"]
        self.latest_data_modifiable["resistance_1"] = levels["resistance_1"]

        return PatternSignalState(
            regime=TREND.UP if level_supportive else TREND.UNKNOWN,
            score=scale_score(
                self.level_tolerance - abs(pivot_distance), self.level_tolerance
            ),
            bullish=level_supportive,
            bearish=False,
            primary_value=pivot_distance,
            signal_value=level_value,
            threshold_value=self.level_tolerance,
            exit_value=levels["resistance_1"],
            aligned_count=2 if level_supportive else 0,
            reason_code="pivot_support_bullish"
            if level_supportive
            else "pivot_not_supportive",
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Pivot",
                "y": [item.get("pivot") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "Support 1",
                "y": [item.get("support_1") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
            {
                "name": "Resistance 1",
                "y": [item.get("resistance_1") for item in self.data_list],
                "line": {"color": "#d62728"},
            },
        ]
