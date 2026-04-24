from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import donchian_channel


class BreakoutDonchianChannelAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:6"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        minimum_breakout: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.minimum_breakout = float(minimum_breakout)
        super().__init__(
            f"breakout_donchian_channel_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=minimum_breakout,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "minimum_breakout": self.minimum_breakout,
            "channel_type": "donchian",
        }

    def _calculate_state(self) -> TrendSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        upper_band, lower_band, middle_band = donchian_channel(highs, lows, self.window)
        prior_upper = upper_band[-2] if len(upper_band) > 1 else None
        prior_lower = lower_band[-2] if len(lower_band) > 1 else None
        current_close = closes[-1]
        current_middle = middle_band[-1]
        self.latest_data_modifiable["donchian_upper"] = prior_upper
        self.latest_data_modifiable["donchian_lower"] = prior_lower
        self.latest_data_modifiable["donchian_middle"] = current_middle
        if prior_upper is None or prior_lower is None or current_middle is None:
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        breakout_up = current_close - prior_upper
        breakout_down = prior_lower - current_close
        bullish = breakout_up > self.minimum_breakout
        bearish = breakout_down > self.minimum_breakout
        channel_width = max(prior_upper - prior_lower, 1e-9)
        signed_breakout = breakout_up if bullish else -breakout_down if bearish else 0.0
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(signed_breakout / channel_width),
            spread=signed_breakout,
            aligned_count=1 if bullish or bearish else 0,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "donchian_breakout_up"
                if bullish
                else "donchian_breakout_down"
                if bearish
                else "donchian_inside_channel"
            ),
            primary_value=current_close,
            signal_value=signed_breakout,
            threshold_value=self.minimum_breakout,
            upper_band=prior_upper,
            lower_band=prior_lower,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Donchian upper",
                "y": [item.get("donchian_upper") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "Donchian lower",
                "y": [item.get("donchian_lower") for item in self.data_list],
                "line": {"color": "#8c564b"},
            },
            {
                "name": "Donchian middle",
                "y": [item.get("donchian_middle") for item in self.data_list],
                "line": {"color": "#7f7f7f", "dash": "dot"},
            },
        ]
