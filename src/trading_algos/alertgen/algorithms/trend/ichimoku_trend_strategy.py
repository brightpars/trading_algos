from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    clamp_unit,
    minimum_history_for_windows,
    safe_relative_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import ichimoku


class IchimokuTrendStrategyAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:11"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        conversion_window: int = 9,
        base_window: int = 26,
        span_b_window: int = 52,
        displacement: int = 26,
        minimum_cloud_gap: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.conversion_window = conversion_window
        self.base_window = base_window
        self.span_b_window = span_b_window
        self.displacement = displacement
        self.minimum_cloud_gap = float(minimum_cloud_gap)
        super().__init__(
            (
                "ichimoku_trend_strategy"
                f"_conv={conversion_window}_base={base_window}_spanb={span_b_window}"
            ),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=minimum_cloud_gap,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return minimum_history_for_windows(
            self.conversion_window,
            self.base_window,
            self.span_b_window,
            self.displacement + 1,
        )

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "conversion_window": self.conversion_window,
            "base_window": self.base_window,
            "span_b_window": self.span_b_window,
            "displacement": self.displacement,
            "minimum_cloud_gap": self.minimum_cloud_gap,
            "indicator": "ichimoku",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "ichimoku_conversion": self.latest_data_modifiable.get(
                "ichimoku_conversion"
            ),
            "ichimoku_base": self.latest_data_modifiable.get("ichimoku_base"),
            "ichimoku_span_a": self.latest_data_modifiable.get("ichimoku_span_a"),
            "ichimoku_span_b": self.latest_data_modifiable.get("ichimoku_span_b"),
            "ichimoku_lagging": self.latest_data_modifiable.get("ichimoku_lagging"),
            "cloud_top": self.latest_data_modifiable.get("cloud_top"),
            "cloud_bottom": self.latest_data_modifiable.get("cloud_bottom"),
            "cloud_gap": self.latest_data_modifiable.get("cloud_gap"),
            "price_cloud_gap": self.latest_data_modifiable.get("price_cloud_gap"),
            "conversion_spread": self.latest_data_modifiable.get("conversion_spread"),
            "lagging_confirmation": self.latest_data_modifiable.get(
                "lagging_confirmation"
            ),
        }

    def _calculate_state(self) -> TrendSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        conversion_line, base_line, span_a, span_b, lagging_span = ichimoku(
            highs,
            lows,
            closes,
            conversion_window=self.conversion_window,
            base_window=self.base_window,
            span_b_window=self.span_b_window,
            displacement=self.displacement,
        )
        conversion_value = conversion_line[-1]
        base_value = base_line[-1]
        span_a_value = span_a[-1]
        span_b_value = span_b[-1]
        lagging_value = lagging_span[-1]
        close_value = closes[-1]
        self.latest_data_modifiable["ichimoku_conversion"] = conversion_value
        self.latest_data_modifiable["ichimoku_base"] = base_value
        self.latest_data_modifiable["ichimoku_span_a"] = span_a_value
        self.latest_data_modifiable["ichimoku_span_b"] = span_b_value
        self.latest_data_modifiable["ichimoku_lagging"] = lagging_value
        if (
            conversion_value is None
            or base_value is None
            or span_a_value is None
            or span_b_value is None
            or lagging_value is None
        ):
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        cloud_top = max(span_a_value, span_b_value)
        cloud_bottom = min(span_a_value, span_b_value)
        cloud_gap = cloud_top - cloud_bottom
        conversion_spread = conversion_value - base_value
        price_cloud_gap = (
            close_value - cloud_top
            if close_value >= cloud_top
            else close_value - cloud_bottom
        )
        lagging_confirmation = lagging_value < close_value
        self.latest_data_modifiable["cloud_top"] = cloud_top
        self.latest_data_modifiable["cloud_bottom"] = cloud_bottom
        self.latest_data_modifiable["cloud_gap"] = cloud_gap
        self.latest_data_modifiable["price_cloud_gap"] = price_cloud_gap
        self.latest_data_modifiable["conversion_spread"] = conversion_spread
        self.latest_data_modifiable["lagging_confirmation"] = lagging_confirmation
        bullish = (
            close_value > cloud_top + self.minimum_cloud_gap
            and conversion_spread > 0.0
            and lagging_confirmation
        )
        bearish = (
            close_value < cloud_bottom - self.minimum_cloud_gap
            and conversion_spread < 0.0
            and not lagging_confirmation
        )
        alignment_count = sum(
            (
                close_value > cloud_top,
                conversion_spread > 0.0,
                lagging_confirmation,
            )
        )
        score = clamp_unit(
            (safe_relative_score(price_cloud_gap, close_value) * 0.5)
            + (safe_relative_score(conversion_spread, close_value) * 0.3)
            + (safe_relative_score(cloud_gap, close_value) * 0.2)
        )
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=score,
            spread=price_cloud_gap,
            aligned_count=alignment_count,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "ichimoku_bullish_cloud_breakout"
                if bullish
                else "ichimoku_bearish_cloud_breakdown"
                if bearish
                else "ichimoku_cloud_neutral"
            ),
            primary_value=close_value,
            signal_value=conversion_spread,
            threshold_value=self.minimum_cloud_gap,
            upper_band=cloud_top,
            lower_band=cloud_bottom,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Ichimoku conversion",
                "y": [item.get("ichimoku_conversion") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Ichimoku base",
                "y": [item.get("ichimoku_base") for item in self.data_list],
                "line": {"color": "#1f77b4"},
            },
            {
                "name": "Ichimoku span A",
                "y": [item.get("ichimoku_span_a") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
            {
                "name": "Ichimoku span B",
                "y": [item.get("ichimoku_span_b") for item in self.data_list],
                "line": {"color": "#d62728"},
            },
        ]
