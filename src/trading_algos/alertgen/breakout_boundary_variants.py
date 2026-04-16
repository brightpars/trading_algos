from trading_algos.alertgen.base import BaseAlertAlgorithm
from trading_algos.alertgen.common import CANDLE_COLOUR, TREND
from trading_algos.alertgen.plotting import (
    PLOT,
    add_normal_graph,
    add_special_graph,
    save_figure,
)

POSITIVE_INFITIY_FLOAT = float("inf")
NEGATIVE_INFITIY_FLOAT = float("-inf")


class BoundaryBreakoutAlertAlgorithm(BaseAlertAlgorithm):
    def __init__(self, symbol, report_base_path, date_str="", evaluate_window_len=5):
        self.alg_name = "boundary_breakout"
        super().__init__(
            self.alg_name, symbol, date_str, evaluate_window_len, report_base_path
        )
        self.low_boundry = POSITIVE_INFITIY_FLOAT
        self.high_boundry = NEGATIVE_INFITIY_FLOAT
        self.colour_list = []
        self.horizontal_line_list = []
        self.no_colourful_candle_seen_yet = True
        self.latest_predicted_trend = TREND.UNKNOWN
        self.breaks_dict = {}

    @property
    def low_boundary(self):
        return self.low_boundry

    @low_boundary.setter
    def low_boundary(self, value):
        self.low_boundry = value

    @property
    def high_boundary(self):
        return self.high_boundry

    @high_boundary.setter
    def high_boundary(self, value):
        self.high_boundry = value

    def update_boundaries(self):
        self.update_boundries()

    def is_low_boundary_broken_lower(self):
        return self.is_low_boundry_broken_lower()

    def is_high_boundary_broken_higher(self):
        return self.is_high_boundry_broken_higher()

    def update_boundries(self):
        if (
            self.latest_predicted_trend == TREND.UP
            and self.latest_candle_colour == CANDLE_COLOUR.GREEN
        ):
            if self.high_boundry < self.latest_data_modifiable["Close"]:
                self.high_boundry = self.latest_data_modifiable["Close"]
        if (
            self.latest_predicted_trend == TREND.DOWN
            and self.latest_candle_colour == CANDLE_COLOUR.RED
        ):
            if self.low_boundry > self.latest_data_modifiable["Close"]:
                self.low_boundry = self.latest_data_modifiable["Close"]

    def is_low_boundry_broken_lower(self):
        return self.low_boundry > self.latest_data_modifiable["Close"]

    def is_high_boundry_broken_higher(self):
        return self.high_boundry < self.latest_data_modifiable["Close"]

    def trend_prediction_logic(self):
        self.set_latest_candle_colour()

        if self.no_colourful_candle_seen_yet:
            if len(self.data_list) == 1:
                return
            self.latest_predicted_trend = self.get_trend_from_candle_colour(
                self.latest_candle_colour
            )
            self.no_colourful_candle_seen_yet = (
                self.latest_candle_colour == CANDLE_COLOUR.WHITE
            )
            self.low_boundry = min(
                self.latest_data_modifiable["Open"],
                self.latest_data_modifiable["Close"],
            )
            self.high_boundry = max(
                self.latest_data_modifiable["Open"],
                self.latest_data_modifiable["Close"],
            )
            if not self.no_colourful_candle_seen_yet:
                self.horizontal_line_list.extend([self.low_boundry, self.high_boundry])
                self.colour_list.extend([CANDLE_COLOUR.RED, CANDLE_COLOUR.GREEN])
                self.breaks_dict["type"] = "init"
                self.breaks_dict["low_boundry"] = self.low_boundry
                self.breaks_dict["high_boundry"] = self.high_boundry
            return

        if self.previous_predicted_trend == TREND.UP:
            if self.is_low_boundry_broken_lower():
                self.latest_predicted_trend = TREND.DOWN
                self.horizontal_line_list.extend([self.low_boundry, self.high_boundry])
                self.colour_list.extend([CANDLE_COLOUR.RED, CANDLE_COLOUR.GREEN])
                self.breaks_dict["type"] = "low_is_broken"
                self.breaks_dict["low_boundry"] = self.low_boundry
                self.breaks_dict["high_boundry"] = self.high_boundry
                self.high_boundry = self.low_boundry
                self.update_boundries()
                return
            self.latest_predicted_trend = TREND.UP
            self.update_boundries()
            return

        if self.previous_predicted_trend == TREND.DOWN:
            if self.is_high_boundry_broken_higher():
                self.latest_predicted_trend = TREND.UP
                self.horizontal_line_list.extend([self.high_boundry, self.low_boundry])
                self.colour_list.extend([CANDLE_COLOUR.GREEN, CANDLE_COLOUR.RED])
                self.breaks_dict["type"] = "high_is_broken"
                self.breaks_dict["low_boundry"] = self.low_boundry
                self.breaks_dict["high_boundry"] = self.high_boundry
                self.low_boundry = self.high_boundry
                self.update_boundries()
                return
            self.latest_predicted_trend = TREND.DOWN
            self.update_boundries()

    def alg_specific_report(self):
        title = f"specific_{self.alg_name}_{self.data_name}"
        add_normal_graph(
            self.data_list,
            (
                ["buy_SIGNAL", "sell_SIGNAL", "no_SIGNAL"],
                PLOT.SEGMENTED,
                ["green", "red", "black"],
            ),
            title=title,
        )
        add_special_graph(
            (PLOT.HORIZONTAL_DASHED, self.horizontal_line_list, self.colour_list),
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
                    "name": "low_boundary",
                    "y": [self.low_boundry for _ in self.data_list]
                    if self.data_list
                    else [],
                    "line": {"color": "red", "dash": "dot"},
                },
                {
                    "name": "high_boundary",
                    "y": [self.high_boundry for _ in self.data_list]
                    if self.data_list
                    else [],
                    "line": {"color": "green", "dash": "dot"},
                },
            ],
        )
        return [(payload, title)] if payload else []


class DoubleRedConfirmationAlertAlgorithm(BoundaryBreakoutAlertAlgorithm):
    def __init__(self, symbol, report_base_path, date_str="", evaluate_window_len=5):
        self.alg_name = "double_red_confirmation"
        BaseAlertAlgorithm.__init__(
            self, self.alg_name, symbol, date_str, evaluate_window_len, report_base_path
        )
        self.low_boundry = POSITIVE_INFITIY_FLOAT
        self.high_boundry = NEGATIVE_INFITIY_FLOAT
        self.colour_list = []
        self.horizontal_line_list = []
        self.no_colourful_candle_seen_yet = True
        self.latest_predicted_trend = TREND.UNKNOWN
        self.breaks_dict = {}
        self.first_red_seen = False
        self.second_red_seen = False

    def update_boundaries(self):
        self.update_boundries()

    def is_low_boundary_broken_lower(self):
        return self.is_low_boundry_broken_lower()

    def is_high_boundary_broken_higher(self):
        return self.is_high_boundry_broken_higher()

    def update_boundries(self):
        if self.is_high_boundry_broken_higher():
            self.high_boundry = self.latest_data_modifiable["High"]
        if self.is_low_boundry_broken_lower():
            self.low_boundry = self.latest_data_modifiable["Low"]

    def is_low_boundry_broken_lower(self):
        return self.latest_data_modifiable["High"] < self.low_boundry

    def is_high_boundry_broken_higher(self):
        return self.latest_data_modifiable["Low"] > self.high_boundry

    def trend_prediction_logic(self):
        BoundaryBreakoutAlertAlgorithm.trend_prediction_logic(self)
        if self.is_high_boundry_broken_higher():
            self.first_red_seen = False
            self.second_red_seen = False
        if self.latest_candle_colour == CANDLE_COLOUR.RED:
            if self.second_red_seen:
                self.first_red_seen = False
                self.second_red_seen = False
                self.latest_predicted_trend = TREND.DOWN
                return
            if self.first_red_seen:
                self.second_red_seen = True
            else:
                self.first_red_seen = True


class LowAnchoredBoundaryBreakoutAlertAlgorithm(BoundaryBreakoutAlertAlgorithm):
    def __init__(self, symbol, report_base_path, date_str="", evaluate_window_len=5):
        self.alg_name = "low_anchored_boundary_breakout"
        BaseAlertAlgorithm.__init__(
            self, self.alg_name, symbol, date_str, evaluate_window_len, report_base_path
        )
        self.low_boundry = POSITIVE_INFITIY_FLOAT
        self.high_boundry = NEGATIVE_INFITIY_FLOAT
        self.colour_list = []
        self.horizontal_line_list = []
        self.no_colourful_candle_seen_yet = True
        self.latest_predicted_trend = TREND.UNKNOWN
        self.breaks_dict = {}
        self.first_red_seen = False
        self.second_red_seen = False

    def update_boundaries(self):
        self.update_boundries()

    def is_low_boundary_broken_lower(self):
        return self.is_low_boundry_broken_lower()

    def is_high_boundary_broken_higher(self):
        return self.is_high_boundry_broken_higher()

    def update_boundries(self):
        if self.is_high_boundry_broken_higher():
            self.high_boundry = self.latest_data_modifiable["High"]
        if self.is_low_boundry_broken_lower():
            self.low_boundry = self.latest_data_modifiable["Low"]

    def is_low_boundry_broken_lower(self):
        return self.low_boundry > self.latest_data_modifiable["Close"]

    def is_high_boundry_broken_higher(self):
        return self.high_boundry < self.latest_data_modifiable["Low"]


alg100 = BoundaryBreakoutAlertAlgorithm
alg101 = DoubleRedConfirmationAlertAlgorithm
alg102 = LowAnchoredBoundaryBreakoutAlertAlgorithm
