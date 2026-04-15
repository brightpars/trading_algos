import logging


LOGGER = logging.getLogger(__name__)
ALERT_TYPE_STRONG_BUY = "strong buy"
ALERT_TYPE_STRONG_SELL = "strong sell"


class alg1:
    def __init__(
        self,
        container_obj,
        confidence_threshold_buy,
        confidence_threshold_sell,
        max_percent_higher_price_buy,
        max_percent_lower_price_sell,
    ) -> None:
        self.container_obj = container_obj
        self.confidence_threshold_buy = confidence_threshold_buy
        self.confidence_threshold_sell = confidence_threshold_sell
        self.max_percent_higher_price_buy = max_percent_higher_price_buy
        self.max_percent_lower_price_sell = max_percent_lower_price_sell

    def process_alerts_list(self, available_alerts_list):
        try:
            for alert in available_alerts_list:
                self.container_obj.mark_alert_as_processed(alert_id=alert["alertID"])
                initiationReason = f"Strong signal on alert/s=[{alert['alertID']}]"
                if alert["alertType"] == ALERT_TYPE_STRONG_BUY:
                    if (
                        alert["alertDetails"]["confidence"]
                        > self.confidence_threshold_buy
                    ):
                        cash_available = (
                            self.container_obj.how_much_usd_available_for_buying()
                        )
                        alert["alertDetails"]["price"] *= (
                            float(100.0 + self.max_percent_higher_price_buy) / 100.0
                        )
                        no_to_buy = int(cash_available / alert["alertDetails"]["price"])
                        if no_to_buy > 0:
                            self.container_obj.submit_buy_operation(
                                alert=alert,
                                no=no_to_buy,
                                initiationReason=initiationReason,
                            )

                if alert["alertType"] == ALERT_TYPE_STRONG_SELL:
                    if (
                        alert["alertDetails"]["confidence"]
                        > self.confidence_threshold_sell
                    ):
                        symbol = alert["alertDetails"]["symbol"]
                        no_to_sell = (
                            self.container_obj.how_many_of_asset_are_available_to_sell(
                                symbol
                            )
                        )
                        alert["alertDetails"]["price"] *= (
                            float(100.0 + self.max_percent_lower_price_sell) / 100.0
                        )
                        if no_to_sell > 0:
                            self.container_obj.submit_sell_operation(
                                alert=alert,
                                no=no_to_sell,
                                initiationReason=initiationReason,
                            )
        except Exception as e:
            LOGGER.error("%s <=> looping over alerts", e)
