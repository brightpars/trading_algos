from __future__ import annotations

from trading_algos.alertgen.algorithms.volatility_options.base import (
    BaseVolatilityAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.volatility_helpers import (
    VolatilitySignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import (
    realized_volatility,
    rolling_mean,
)


class VolatilityMeanReversionAlertAlgorithm(BaseVolatilityAlertAlgorithm):
    catalog_ref = "algorithm:54"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        volatility_window: int = 5,
        baseline_window: int = 8,
        high_threshold: float = 1.2,
        low_threshold: float = 0.8,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.volatility_window = volatility_window
        self.baseline_window = baseline_window
        self.high_threshold = float(high_threshold)
        self.low_threshold = float(low_threshold)
        super().__init__(
            f"volatility_mean_reversion_vol={volatility_window}_base={baseline_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.volatility_window + self.baseline_window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "volatility_window": self.volatility_window,
            "baseline_window": self.baseline_window,
            "high_threshold": self.high_threshold,
            "low_threshold": self.low_threshold,
            "indicator": "realized_volatility_ratio",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "realized_volatility": self.latest_data_modifiable.get(
                "realized_volatility"
            ),
            "volatility_baseline": self.latest_data_modifiable.get(
                "volatility_baseline"
            ),
            "volatility_ratio": self.latest_data_modifiable.get("volatility_ratio"),
        }

    def _calculate_state(self) -> VolatilitySignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        volatility_values = realized_volatility(closes, self.volatility_window)
        baseline_values = rolling_mean(volatility_values, self.baseline_window)
        volatility_value = volatility_values[-1]
        baseline_value = baseline_values[-1]
        ratio_value = None
        if volatility_value is not None and baseline_value not in (None, 0.0):
            assert baseline_value is not None
            ratio_value = volatility_value / baseline_value
        self.latest_data_modifiable["realized_volatility"] = volatility_value
        self.latest_data_modifiable["volatility_baseline"] = baseline_value
        self.latest_data_modifiable["volatility_ratio"] = ratio_value
        if ratio_value is None:
            return VolatilitySignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=baseline_value,
                threshold_value=self.high_threshold,
                exit_value=1.0,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = ratio_value <= self.low_threshold
        bearish = ratio_value >= self.high_threshold
        return VolatilitySignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(
                1.0 - ratio_value,
                max(abs(self.high_threshold - 1.0), abs(1.0 - self.low_threshold), 0.1),
            ),
            bullish=bullish,
            bearish=bearish,
            primary_value=ratio_value,
            signal_value=baseline_value,
            threshold_value=self.low_threshold if bullish else self.high_threshold,
            exit_value=1.0,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "volatility_ratio_low"
                if bullish
                else "volatility_ratio_high"
                if bearish
                else "volatility_ratio_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Realized Volatility",
                "y": [item.get("realized_volatility") for item in self.data_list],
                "line": {"color": "#8c564b"},
            },
            {
                "name": "Volatility Baseline",
                "y": [item.get("volatility_baseline") for item in self.data_list],
                "line": {"color": "#17becf"},
            },
            {
                "name": "Volatility Ratio",
                "y": [item.get("volatility_ratio") for item in self.data_list],
                "line": {"color": "#bcbd22"},
                "yaxis": "y2",
            },
        ]
