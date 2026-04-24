from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    rolling_ou_reversion_ratio,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class OrnsteinUhlenbeckReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:35"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 8,
        entry_sigma: float = 1.0,
        exit_sigma: float = 0.35,
        min_mean_reversion_speed: float = 0.05,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = int(window)
        self.entry_sigma = float(entry_sigma)
        self.exit_sigma = float(exit_sigma)
        self.min_mean_reversion_speed = float(min_mean_reversion_speed)
        super().__init__(
            f"ornstein_uhlenbeck_reversion_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "entry_sigma": self.entry_sigma,
            "exit_sigma": self.exit_sigma,
            "min_mean_reversion_speed": self.min_mean_reversion_speed,
            "indicator": "ou_residual_zscore",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "ou_mean_reversion_speed": self.latest_data_modifiable.get(
                "ou_mean_reversion_speed"
            ),
            "ou_speed_ready": self.latest_data_modifiable.get("ou_speed_ready"),
            "ou_equilibrium": self.latest_data_modifiable.get("ou_equilibrium"),
            "ou_residual": self.latest_data_modifiable.get("ou_residual"),
            "ou_residual_zscore": self.latest_data_modifiable.get("ou_residual_zscore"),
        }

    def _warmup_ready(self, state: MeanReversionSignalState) -> bool:
        return bool(self.latest_data_modifiable.get("ou_speed_ready", False))

    def _calculate_state(self) -> MeanReversionSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        speeds, equilibria, residuals, zscores = rolling_ou_reversion_ratio(
            closes, self.window
        )
        mean_reversion_speed = speeds[-1]
        equilibrium = equilibria[-1]
        residual = residuals[-1]
        residual_zscore = zscores[-1]

        self.latest_data_modifiable["ou_mean_reversion_speed"] = mean_reversion_speed
        self.latest_data_modifiable["ou_speed_ready"] = (
            mean_reversion_speed is not None
            and equilibrium is not None
            and residual is not None
            and residual_zscore is not None
        )
        self.latest_data_modifiable["ou_equilibrium"] = equilibrium
        self.latest_data_modifiable["ou_residual"] = residual
        self.latest_data_modifiable["ou_residual_zscore"] = residual_zscore

        if (
            mean_reversion_speed is None
            or equilibrium is None
            or residual is None
            or residual_zscore is None
        ):
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=equilibrium,
                threshold_value=-self.entry_sigma,
                exit_value=self.exit_sigma,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        speed_ok = mean_reversion_speed >= self.min_mean_reversion_speed
        bullish = speed_ok and residual_zscore <= -self.entry_sigma
        bearish = speed_ok and residual_zscore >= self.entry_sigma
        if not speed_ok:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=residual_zscore,
                signal_value=equilibrium,
                threshold_value=self.min_mean_reversion_speed,
                exit_value=self.exit_sigma,
                aligned_count=0,
                reason_code="ou_speed_below_threshold",
            )

        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-residual_zscore, self.entry_sigma),
            bullish=bullish,
            bearish=bearish,
            primary_value=residual_zscore,
            signal_value=equilibrium,
            threshold_value=-self.entry_sigma if bullish else self.entry_sigma,
            exit_value=self.exit_sigma,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "ou_oversold"
                if bullish
                else "ou_overbought"
                if bearish
                else "ou_inside_band"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "OU Equilibrium",
                "y": [item.get("ou_equilibrium") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "OU Residual Z-Score",
                "y": [item.get("ou_residual_zscore") for item in self.data_list],
                "line": {"color": "#9467bd"},
                "yaxis": "y2",
            },
        ]
