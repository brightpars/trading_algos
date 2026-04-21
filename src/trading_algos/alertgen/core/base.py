import copy
import logging
import os
from abc import ABC, abstractmethod

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
)
from trading_algos.alertgen.shared_utils.common import CANDLE_COLOUR, TREND
from trading_algos.alertgen.shared_utils.evaluation import (
    calculate_ground_truth,
    evaluate_predictions,
)
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
    Candle,
)
from trading_algos.alertgen.shared_utils.plotting import (
    PLOT,
    add_normal_graph,
    save_figure,
)
from trading_algos.alertgen.shared_utils.reporting import write_analysis_report_bundle


LOGGER = logging.getLogger(__name__)
DEFAULT_FIGURE_W = 12
DEFAULT_FIGURE_L = 4


class BaseAlertAlgorithm(ABC):
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
        self.latest_predicted_trend_confidence = 0.0

    @property
    def buy_signals(self):
        return self.buy_SIGNALS

    @property
    def sell_signals(self):
        return self.sell_SIGNALS

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

    @abstractmethod
    def trend_prediction_logic(self):
        """Set latest trend-related fields for the most recent candle."""

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
        self.latest_decision = self.current_decision()

    def process(self, data):
        self.previous_predicted_trend = self.latest_predicted_trend
        try:
            self.previous_data = self.latest_data
        except Exception:
            pass

        self.latest_candle = Candle.from_mapping(data)
        self.latest_data = self.latest_candle.to_mapping()
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
        calculate_ground_truth(self.data_list, self.evaluate_window_len)

    def evaluate(self):
        self.calculate_ground_truth()
        self.eval_dict = evaluate_predictions(
            self.data_list, self.predicted_trend_list
        ).metrics

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

    def algorithm_metadata(self):
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def minimum_history(self) -> int:
        return 1

    def current_decision(self):
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == TREND.UP,
            sell_signal=self.latest_predicted_trend == TREND.DOWN,
            buy_range_signal=self.latest_predicted_trend == TREND.RANGE_UP,
            sell_range_signal=self.latest_predicted_trend == TREND.RANGE_DOWN,
            no_signal=self.latest_predicted_trend not in [TREND.UP, TREND.DOWN],
            annotations={"alg_name": self.alg_name},
        )

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
        write_analysis_report_bundle(
            report_path=self.report_path,
            data_name=self.data_name,
            data_list=self.data_list,
            eval_dict=self.eval_dict,
            make_standard_figure=self.make_standard_figure,
            make_ground_truth_figure=self.make_ground_truth_figure,
            alg_specific_report=self.alg_specific_report,
            figure_w=DEFAULT_FIGURE_W,
            figure_l=DEFAULT_FIGURE_L,
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        points = []
        for item in self.data_list:
            if item.get("buy_SIGNAL"):
                signal_label = "buy"
            elif item.get("sell_SIGNAL"):
                signal_label = "sell"
            else:
                signal_label = "neutral"
            points.append(
                AlertSeriesPoint(
                    timestamp=str(item.get("ts", "")),
                    signal_label=signal_label,
                    confidence=float(item.get("trend_confidence", 0.0) or 0.0),
                )
            )
        derived_series = {
            "close": self._close_values(),
            "buy_signal": [bool(item.get("buy_SIGNAL")) for item in self.data_list],
            "sell_signal": [bool(item.get("sell_SIGNAL")) for item in self.data_list],
            "gt_trend": [item.get("gt_trend") for item in self.data_list],
        }
        for key in self.data_list[-1].keys() if self.data_list else []:
            if key in {
                "ts",
                "Open",
                "High",
                "Low",
                "Close",
                "buy_SIGNAL",
                "sell_SIGNAL",
                "no_SIGNAL",
                "trend_confidence",
                "gt_trend",
                "gt_up",
                "gt_down",
                "gt_nn",
            }:
                continue
            derived_series[key] = [item.get(key) for item in self.data_list]
        return AlertAlgorithmOutput(
            algorithm_key=self.alg_name,
            points=tuple(points),
            derived_series=derived_series,
            summary_metrics=dict(self.eval_dict),
            metadata={
                "algorithm_name": self.alg_name,
                "family": "trend",
                "symbol": self.symbol,
                "warmup_period": self.minimum_history(),
                "evaluate_window_len": self.evaluate_window_len,
            },
        )
