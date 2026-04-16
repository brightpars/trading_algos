from trading_algos.alertgen.core.base import BaseAlertAlgorithm
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.plotting import (
    PLOT,
    add_normal_graph,
    save_figure,
)


class RollingChannelBreakoutAlertAlgorithm(BaseAlertAlgorithm):
    class State:
        INIT = "init"
        BREAK_LOW = "break_low"
        BREAK_LOW_SEEN = "break_low_seen"
        BREAK_HIGH = "break_high"
        BREAK_HIGH_SEEN = "break_high_seen"
        BETWEEN_BREAK_LINES = "between_break_lines"

    def __init__(
        self, symbol, report_base_path, date_str="", evaluate_window_len=5, wlen=20
    ):
        self.alg_name = f"rolling_channel_breakout_wlen={wlen}"
        super().__init__(
            self.alg_name, symbol, date_str, evaluate_window_len, report_base_path
        )
        self.wlen = wlen
        self.latest_predicted_trend = TREND.UNKNOWN
        self.state = self.State.INIT

    def minimum_history(self) -> int:
        return self.wlen

    def trend_prediction_logic(self):
        if len(self.data_list) < 2:
            self.latest_predicted_trend = TREND.UNKNOWN
            self.latest_data_modifiable["avg_low"] = self.latest_data_modifiable["Low"]
            self.latest_data_modifiable["avg_high"] = self.latest_data_modifiable[
                "High"
            ]
            return

        sum_low = 0.0
        sum_high = 0.0
        for data in self.data_list[-self.wlen :]:
            sum_low += data["Low"]
            sum_high += data["High"]
        avg_low = sum_low / len(self.data_list[-self.wlen :])
        avg_high = sum_high / len(self.data_list[-self.wlen :])
        self.latest_data_modifiable["avg_low"] = avg_low
        self.latest_data_modifiable["avg_high"] = avg_high

        if self.latest_data_modifiable["Close"] > avg_high:
            if self.state == self.State.BREAK_HIGH:
                self.state = self.State.BREAK_HIGH_SEEN
            elif self.state != self.State.BREAK_HIGH_SEEN:
                self.state = self.State.BREAK_HIGH
        elif self.latest_data_modifiable["Close"] < avg_low:
            if self.state == self.State.BREAK_LOW:
                self.state = self.State.BREAK_LOW_SEEN
            elif self.state != self.State.BREAK_LOW_SEEN:
                self.state = self.State.BREAK_LOW
        else:
            self.state = self.State.BETWEEN_BREAK_LINES

        if len(self.data_list) > self.wlen:
            if self.state == self.State.BREAK_HIGH:
                self.latest_predicted_trend = TREND.UP
            if self.state == self.State.BREAK_LOW:
                self.latest_predicted_trend = TREND.DOWN
            if self.state == self.State.BETWEEN_BREAK_LINES:
                self.latest_predicted_trend = TREND.UNKNOWN
        else:
            self.latest_predicted_trend = TREND.UNKNOWN

    def alg_specific_report(self):
        title = f"specific_{self.alg_name}_{self.data_name}"
        add_normal_graph(self.data_list, ("avg_low", PLOT.PLOT), title=title)
        add_normal_graph(self.data_list, ("avg_high", PLOT.PLOT), title=title)
        add_normal_graph(
            self.data_list,
            (
                ["buy_SIGNAL", "sell_SIGNAL", "no_SIGNAL"],
                PLOT.SEGMENTED,
                ["green", "red", "black"],
            ),
            title=title,
        )
        filename = f"specific_{self.data_name}"
        return [
            (
                save_figure(path=self.report_path, filename=filename, overwrite=True),
                title,
            )
        ]

    def interactive_report_payloads(self):
        title = f"specific_{self.alg_name}_{self.data_name}"
        payload = self._build_default_signal_chart_payload(
            title=title,
            extra_series=[
                {
                    "name": "avg_low",
                    "y": [item.get("avg_low") for item in self.data_list],
                    "line": {"color": "orange"},
                },
                {
                    "name": "avg_high",
                    "y": [item.get("avg_high") for item in self.data_list],
                    "line": {"color": "purple"},
                },
            ],
        )
        return [(payload, title)] if payload else []


class CloseHighChannelBreakoutAlertAlgorithm(RollingChannelBreakoutAlertAlgorithm):
    def __init__(
        self, symbol, report_base_path, date_str="", evaluate_window_len=5, wlen=20
    ):
        self.alg_name = f"close_high_channel_breakout_wlen={wlen}"
        BaseAlertAlgorithm.__init__(
            self, self.alg_name, symbol, date_str, evaluate_window_len, report_base_path
        )
        self.wlen = wlen
        self.latest_predicted_trend = TREND.UNKNOWN
        self.state = self.State.INIT

    def minimum_history(self) -> int:
        return self.wlen

    def trend_prediction_logic(self):
        if len(self.data_list) < 2:
            self.latest_predicted_trend = TREND.UNKNOWN
            self.latest_data_modifiable["avg_low"] = self.latest_data_modifiable[
                "Close"
            ]
            self.latest_data_modifiable["avg_high"] = self.latest_data_modifiable[
                "High"
            ]
            return

        sum_low = 0.0
        sum_high = 0.0
        for data in self.data_list[-self.wlen :]:
            sum_low += data["Close"]
            sum_high += data["High"]
        avg_low = sum_low / len(self.data_list[-self.wlen :])
        avg_high = sum_high / len(self.data_list[-self.wlen :])
        self.latest_data_modifiable["avg_low"] = avg_low
        self.latest_data_modifiable["avg_high"] = avg_high

        if self.latest_data_modifiable["Close"] > avg_high:
            if self.state == self.State.BREAK_HIGH:
                self.state = self.State.BREAK_HIGH_SEEN
            elif self.state != self.State.BREAK_HIGH_SEEN:
                self.state = self.State.BREAK_HIGH
        elif self.latest_data_modifiable["Close"] < avg_low:
            if self.state == self.State.BREAK_LOW:
                self.state = self.State.BREAK_LOW_SEEN
            elif self.state != self.State.BREAK_LOW_SEEN:
                self.state = self.State.BREAK_LOW
        else:
            self.state = self.State.BETWEEN_BREAK_LINES

        if len(self.data_list) > self.wlen:
            if self.state == self.State.BREAK_HIGH:
                self.latest_predicted_trend = TREND.UP
            if self.state == self.State.BREAK_LOW:
                self.latest_predicted_trend = TREND.DOWN
            if self.state == self.State.BETWEEN_BREAK_LINES:
                self.latest_predicted_trend = TREND.UNKNOWN
        else:
            self.latest_predicted_trend = TREND.UNKNOWN
