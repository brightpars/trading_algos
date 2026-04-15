import copy
import json
import logging
import os

import matplotlib.pyplot as plt
from scipy import stats

from trading_algos.alertgen.common import CANDLE_COLOUR, TREND
from trading_algos.alertgen.plotting import PLOT, add_normal_graph, save_figure


LOGGER = logging.getLogger(__name__)
DEFAULT_FIGURE_W = 12
DEFAULT_FIGURE_L = 4


class BaseAlertAlgorithm:
    def __init__(
        self, alg_name, symbol, date_str, evaluate_window_len, report_base_path
    ):
        self.alg_name = alg_name
        self.symbol = symbol
        self.date = date_str
        self.data_name = f"{symbol}_{date_str}" if self.date != "" else f"{symbol}"

        self.data_list = []
        self.predicted_trend_list = []
        self.buy_SIGNALS = []
        self.sell_SIGNALS = []
        self.eval_dict = {}

        base_path = os.path.join(report_base_path, self.alg_name)
        os.makedirs(base_path, exist_ok=True)
        self.report_path = os.path.join(base_path, self.symbol)
        os.makedirs(self.report_path, exist_ok=True)
        self.evaluate_window_len = evaluate_window_len
        self.previous_predicted_trend = TREND.UNKNOWN
        self.latest_predicted_trend = TREND.UNKNOWN

    def set_latest_candle_colour(self):
        data = self.latest_data
        self.latest_candle_colour = (
            CANDLE_COLOUR.GREEN
            if data["Close"] > data["Open"]
            else CANDLE_COLOUR.RED
            if data["Close"] < data["Open"]
            else CANDLE_COLOUR.WHITE
        )

    def get_trend_from_candle_colour(self, colour):
        if colour == CANDLE_COLOUR.GREEN:
            return TREND.UP
        if colour == CANDLE_COLOUR.RED:
            return TREND.DOWN
        return TREND.UNKNOWN

    def set_standard_trend_confidence(self):
        if len(self.predicted_trend_list) <= 2:
            self.latest_predicted_trend_confidence = 4.0
            return
        if self.predicted_trend_list[-2] != self.latest_predicted_trend:
            self.latest_predicted_trend_confidence = 10.0
            return
        if len(self.predicted_trend_list) <= 3:
            self.latest_predicted_trend_confidence = 4.0
            return
        if self.predicted_trend_list[-3] != self.latest_predicted_trend:
            self.latest_predicted_trend_confidence = 8.0
            return
        if len(self.predicted_trend_list) <= 4:
            self.latest_predicted_trend_confidence = 4.0
            return
        if self.predicted_trend_list[-4] != self.latest_predicted_trend:
            self.latest_predicted_trend_confidence = 6.0
            return
        self.latest_predicted_trend_confidence = 4.0

    def trend_prediction_logic(self):
        LOGGER.error(
            "trend_prediction_logic must be implemented in subclass and sets values for self.latest_predicted_trend and self.latest_predicted_trend_confidence"
        )
        self.latest_predicted_trend = TREND.UNKNOWN

    def do_trend_prediction(self):
        self.trend_prediction_logic()
        self.predicted_trend_list.append(self.latest_predicted_trend)
        self.set_standard_trend_confidence()
        self.latest_data_modifiable["trend_confidence"] = (
            self.latest_predicted_trend_confidence
        )
        if self.latest_predicted_trend == TREND.UP:
            self.latest_data_modifiable["buy_SIGNAL"] = True
            self.buy_SIGNALS.append(self.latest_data_modifiable)
        else:
            self.latest_data_modifiable["buy_SIGNAL"] = False

        if self.latest_predicted_trend == TREND.DOWN:
            self.latest_data_modifiable["sell_SIGNAL"] = True
            self.sell_SIGNALS.append(self.latest_data_modifiable)
        else:
            self.latest_data_modifiable["sell_SIGNAL"] = False

        self.latest_data_modifiable["no_SIGNAL"] = self.latest_predicted_trend not in [
            TREND.UP,
            TREND.DOWN,
        ]
        self.latest_data_modifiable["sell_RANGE_SIGNAL"] = (
            self.latest_predicted_trend == TREND.RANGE_DOWN
        )
        self.latest_data_modifiable["buy_RANGE_SIGNAL"] = (
            self.latest_predicted_trend == TREND.RANGE_UP
        )

    def process(self, data):
        self.previous_predicted_trend = self.latest_predicted_trend
        try:
            self.previous_data = self.latest_data
        except Exception:
            pass

        self.latest_data = data
        self.latest_data_modifiable = copy.deepcopy(self.latest_data)
        self.data_list.append(self.latest_data_modifiable)
        self.do_trend_prediction()

    def process_list(self, dataList):
        for data in copy.deepcopy(dataList):
            self.process(data)

    def set_gt_in_data(self, idx, gt):
        self.data_list[idx]["gt_up"] = gt == TREND.UP
        self.data_list[idx]["gt_down"] = gt == TREND.DOWN
        self.data_list[idx]["gt_nn"] = gt not in [TREND.UP, TREND.DOWN]
        self.data_list[idx]["gt_trend"] = gt

    def calculate_ground_truth(self):
        last_idx = len(self.data_list) - 1
        self.evaluate_window_len = 5
        first_colourful_idx = last_idx - self.evaluate_window_len

        for idx in range(last_idx, first_colourful_idx - 1, -1):
            self.set_gt_in_data(idx, TREND.UNKNOWN)

        for idx in range(first_colourful_idx - 1, -1, -1):
            y = [
                self.data_list[idx]["Close"],
                self.data_list[idx + self.evaluate_window_len - 1]["Close"],
            ]
            x = [1, self.evaluate_window_len]
            slope, _, r, _, _ = stats.linregress(x, y)
            if abs(r) < 0.7:
                gt = self.data_list[idx + 1]["gt_trend"]
            else:
                threshold = 0.001
                if slope > threshold:
                    gt = TREND.UP
                elif slope < -threshold:
                    gt = TREND.DOWN
                else:
                    gt = self.data_list[idx + 1]["gt_trend"]
            self.set_gt_in_data(idx, gt)

        while True:
            do_changed = False
            for idx in range(first_colourful_idx - 3, -1, -1):
                begin_idx = idx
                mid_idx = idx + 1
                end_idx = idx + 2
                if (
                    self.data_list[begin_idx]["gt_trend"]
                    == self.data_list[end_idx]["gt_trend"]
                ):
                    if (
                        self.data_list[begin_idx]["gt_trend"]
                        != self.data_list[mid_idx]["gt_trend"]
                    ):
                        gt = self.data_list[begin_idx]["gt_trend"]
                        self.set_gt_in_data(mid_idx, gt)
                        do_changed = True
            if do_changed is False:
                break

        while True:
            do_changed = False
            for idx in range(first_colourful_idx - 4, -1, -1):
                begin_idx = idx
                mid_idx = idx + 1
                end_idx = idx + 3
                if (
                    self.data_list[begin_idx]["gt_trend"]
                    == self.data_list[end_idx]["gt_trend"]
                ):
                    if (
                        self.data_list[begin_idx]["gt_trend"]
                        != self.data_list[mid_idx]["gt_trend"]
                    ):
                        gt = self.data_list[begin_idx]["gt_trend"]
                        self.set_gt_in_data(mid_idx, gt)
                        self.set_gt_in_data(mid_idx + 1, gt)
                        do_changed = True
            if do_changed is False:
                break

    def evaluate(self):
        correct_prediction_no = 0
        wrong_prediction_no = 0
        absolute_wrong_no = 0
        correct_buy_signal_no = 0
        correct_sell_signal_no = 0

        self.calculate_ground_truth()
        for idx, predicted_trend in enumerate(self.predicted_trend_list):
            ground_truth_trend = self.data_list[idx]["gt_trend"]
            if predicted_trend == ground_truth_trend:
                correct_prediction_no += 1
            else:
                wrong_prediction_no += 1
            if ground_truth_trend == TREND.UP and predicted_trend == TREND.DOWN:
                absolute_wrong_no += 1
            if ground_truth_trend == TREND.DOWN and predicted_trend == TREND.UP:
                absolute_wrong_no += 1
            if predicted_trend == TREND.UP and ground_truth_trend == TREND.UP:
                correct_buy_signal_no += 1
            if predicted_trend == TREND.DOWN and ground_truth_trend == TREND.DOWN:
                correct_sell_signal_no += 1

        self.eval_dict["B~"] = len(self.buy_SIGNALS)
        self.eval_dict["B+"] = correct_buy_signal_no
        self.eval_dict["S~"] = len(self.sell_SIGNALS)
        self.eval_dict["S+"] = correct_sell_signal_no
        self.eval_dict["!!"] = absolute_wrong_no

    def make_standard_figure(self, save=True):
        title = f"{self.alg_name}_{self.data_name}"
        add_normal_graph(
            self.data_list,
            (
                ["buy_SIGNAL", "sell_SIGNAL", "no_SIGNAL"],
                PLOT.SEGMENTED,
                ["green", "red", "black"],
            ),
            title=title,
        )
        if save:
            save_figure(path=self.report_path, filename=self.data_name)

    def make_ground_truth_figure(self, save=True):
        title = f"ground-truth {self.data_name}"
        add_normal_graph(
            self.data_list,
            (["gt_up", "gt_down", "gt_nn"], PLOT.SEGMENTED, ["green", "red", "black"]),
            title=title,
        )
        if save:
            save_figure(path=self.report_path, filename=f"{self.data_name}_gt")

    def alg_specific_report(self):
        return []

    def interactive_report_payloads(self):
        return []

    def _ts_values_as_strings(self):
        return [str(item.get("ts"))[2:] for item in self.data_list]

    def _close_values(self):
        return [item.get("Close") for item in self.data_list]

    def _signal_marker_values(self, key):
        return [item.get("Close") if item.get(key) else None for item in self.data_list]

    def _build_plotly_chart(self, title, series_list, y_axis_title="Price"):
        return {
            "data": [
                {
                    "type": series.get("type", "scatter"),
                    "mode": series.get("mode", "lines"),
                    "name": series.get("name", "series"),
                    "x": self._ts_values_as_strings(),
                    "y": series.get("y", []),
                    "line": series.get("line", {}),
                    "marker": series.get("marker", {}),
                }
                for series in series_list
            ],
            "layout": {
                "title": {"text": title},
                "xaxis": {"title": "Execution time"},
                "yaxis": {"title": y_axis_title},
                "hovermode": "x unified",
                "legend": {"orientation": "h"},
                "margin": {"l": 60, "r": 30, "t": 60, "b": 60},
                "paper_bgcolor": "white",
                "plot_bgcolor": "white",
            },
            "config": {
                "responsive": True,
                "displaylogo": False,
                "scrollZoom": True,
            },
        }

    def _build_default_signal_chart_payload(self, title, extra_series=None):
        if not self.data_list:
            return None
        series_list = [
            {"name": "Close", "y": self._close_values(), "line": {"color": "#1f77b4"}},
            {
                "name": "buy_SIGNAL",
                "y": self._signal_marker_values("buy_SIGNAL"),
                "mode": "markers",
                "marker": {"color": "green", "size": 9},
            },
            {
                "name": "sell_SIGNAL",
                "y": self._signal_marker_values("sell_SIGNAL"),
                "mode": "markers",
                "marker": {"color": "red", "size": 9},
            },
        ]
        if extra_series:
            series_list.extend(extra_series)
        return self._build_plotly_chart(title=title, series_list=series_list)

    def write_analysis_report(self):
        fig, axes = plt.subplots(
            ncols=1, nrows=2, gridspec_kw={"height_ratios": [2, 1]}
        )

        plt.sca(axes[0])
        self.make_standard_figure(save=False)
        fig.add_subplot(axes[0])

        plt.sca(axes[1])
        self.make_ground_truth_figure(save=False)
        fig.add_subplot(axes[1])

        fig.set_size_inches(
            DEFAULT_FIGURE_W,
            3 * DEFAULT_FIGURE_L,
        )
        plt.tight_layout()

        save_figure(path=self.report_path, filename=self.data_name)
        path = os.path.join(self.report_path, self.data_name + ".dict")
        data_list_copy = copy.deepcopy(self.data_list)
        for data in data_list_copy:
            data.pop("_id", None)
            data["ts"] = str(data["ts"])
        dicta = {"data": data_list_copy, "eval_dict": self.eval_dict}
        with open(path, "w") as fp:
            json.dump(dicta, fp)

        self.alg_specific_report()
