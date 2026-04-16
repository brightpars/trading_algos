import logging

from trading_algos.alertgen.core.base import BaseAlertAlgorithm
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.plotting import (
    PLOT,
    add_normal_graph,
    save_figure,
)


LOGGER = logging.getLogger(__name__)


class agreegate_algs(BaseAlertAlgorithm):
    class Method:
        Or = "|"
        And = "&"

    AggregateMethod = Method

    def __init__(
        self,
        symbol,
        report_base_path,
        buy_algs_obj_list=None,
        sell_algs_obj_list=None,
        buy_method=Method.And,
        sell_method=Method.Or,
        date_str="",
        evaluate_window_len=5,
    ):
        buy_algs_obj_list = buy_algs_obj_list or []
        sell_algs_obj_list = sell_algs_obj_list or []

        name_algs_buy = ""
        self.buy_method = buy_method
        for alg_obj in buy_algs_obj_list:
            if name_algs_buy != "":
                name_algs_buy += buy_method
            else:
                name_algs_buy += "Buy{"
            name_algs_buy += alg_obj.alg_name
        name_algs_buy += "}"

        name_algs_sell = ""
        self.sell_method = sell_method
        for alg_obj in sell_algs_obj_list:
            if name_algs_sell != "":
                name_algs_sell += sell_method
            else:
                name_algs_sell += "Sell{"
            name_algs_sell += alg_obj.alg_name
        name_algs_sell += "}"

        self.alg_name = f"agreegate_<{name_algs_buy},{name_algs_sell}>"
        super().__init__(
            self.alg_name, symbol, date_str, evaluate_window_len, report_base_path
        )
        self.buy_algs_obj_list = buy_algs_obj_list
        self.sell_algs_obj_list = sell_algs_obj_list

    def composition_metadata(self):
        return {
            "buy_method": self.buy_method,
            "sell_method": self.sell_method,
            "buy_algorithms": [alg.alg_name for alg in self.buy_algs_obj_list],
            "sell_algorithms": [alg.alg_name for alg in self.sell_algs_obj_list],
        }

    def trend_prediction_logic(self):
        for alg_obj in self.buy_algs_obj_list:
            alg_obj.process(self.latest_data)
        for alg_obj in self.sell_algs_obj_list:
            alg_obj.process(self.latest_data)

        self.latest_predicted_trend_list_buy = [
            (alg_obj.latest_predicted_trend, alg_obj.latest_predicted_trend_confidence)
            for alg_obj in self.buy_algs_obj_list
        ]
        self.latest_predicted_trend_list_sell = [
            (alg_obj.latest_predicted_trend, alg_obj.latest_predicted_trend_confidence)
            for alg_obj in self.sell_algs_obj_list
        ]
        self.aggregate_trends_and_set_confidence()

    def aggregate_trends_and_set_confidence(self):
        if self.buy_method == self.Method.And:
            buy_aggreegate_result = True
            buy_trend_confidence = 10.0
            for (
                latest_predicted_trend,
                latest_predicted_trend_confidence,
            ) in self.latest_predicted_trend_list_buy:
                if latest_predicted_trend != TREND.UP:
                    buy_aggreegate_result = False
                if latest_predicted_trend == TREND.UP:
                    buy_trend_confidence = min(
                        buy_trend_confidence, latest_predicted_trend_confidence
                    )
        else:
            buy_aggreegate_result = False
            buy_trend_confidence = 0.0
            for (
                latest_predicted_trend,
                latest_predicted_trend_confidence,
            ) in self.latest_predicted_trend_list_buy:
                if latest_predicted_trend == TREND.UP:
                    buy_aggreegate_result = True
                    buy_trend_confidence = max(
                        buy_trend_confidence, latest_predicted_trend_confidence
                    )

        if self.sell_method == self.Method.And:
            sell_aggreegate_result = True
            sell_trend_confidence = 10.0
            for (
                latest_predicted_trend,
                latest_predicted_trend_confidence,
            ) in self.latest_predicted_trend_list_sell:
                if latest_predicted_trend != TREND.DOWN:
                    sell_aggreegate_result = False
                if latest_predicted_trend == TREND.DOWN:
                    sell_trend_confidence = min(
                        sell_trend_confidence, latest_predicted_trend_confidence
                    )
        else:
            sell_aggreegate_result = False
            sell_trend_confidence = 0.0
            for (
                latest_predicted_trend,
                latest_predicted_trend_confidence,
            ) in self.latest_predicted_trend_list_sell:
                if latest_predicted_trend == TREND.DOWN:
                    sell_aggreegate_result = True
                    sell_trend_confidence = max(
                        sell_trend_confidence, latest_predicted_trend_confidence
                    )

        if sell_aggreegate_result:
            self.latest_predicted_trend = TREND.DOWN
            self.latest_predicted_trend_confidence = sell_trend_confidence
            LOGGER.debug(
                "%s => %s, %s",
                self.latest_predicted_trend_list_sell,
                self.latest_predicted_trend,
                self.latest_predicted_trend_confidence,
            )
            return
        if buy_aggreegate_result:
            self.latest_predicted_trend = TREND.UP
            self.latest_predicted_trend_confidence = buy_trend_confidence
            LOGGER.debug(
                "%s => %s, %s",
                self.latest_predicted_trend_list_buy,
                self.latest_predicted_trend,
                self.latest_predicted_trend_confidence,
            )
            return
        self.latest_predicted_trend = TREND.UNKNOWN
        self.latest_predicted_trend_confidence = 10.0

    def agreegate_trends_and_set_confidence(self):
        self.aggregate_trends_and_set_confidence()

    def alg_specific_report(self):
        result = []
        for alg in self.buy_algs_obj_list:
            result.extend(alg.alg_specific_report())
        for alg in self.sell_algs_obj_list:
            result.extend(alg.alg_specific_report())

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
        filename = f"specific_{self.data_name}"
        result.append(
            (
                save_figure(path=self.report_path, filename=filename, overwrite=True),
                title,
            )
        )
        return result

    def interactive_report_payloads(self):
        result = []
        for alg in self.buy_algs_obj_list:
            result.extend(alg.interactive_report_payloads())
        for alg in self.sell_algs_obj_list:
            result.extend(alg.interactive_report_payloads())
        title = f"specific_{self.alg_name}_{self.data_name}"
        payload = self._build_default_signal_chart_payload(title=title)
        if payload:
            result.append((payload, title))
        return result