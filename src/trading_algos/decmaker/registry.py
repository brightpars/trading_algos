DEFAULT_DECMAKER_CONFIDENCE_THRESHOLD_BUY = 9.0
DEFAULT_DECMAKER_CONFIDENCE_THRESHOLD_SELL = 9.0
DEFAULT_DECMAKER_MAX_PERCENT_HIGHER_PRICE_BUY = 0.0
DEFAULT_DECMAKER_MAX_PERCENT_LOWER_PRICE_SELL = 0.0


def get_default_decmaker_engine_config(name="decmaker_0"):
    return {
        "name": name,
        "enable": True,
        "engine_config": {
            "type": "dec1",
            "interval_secs": 60,
            "confidence_threshold_buy": DEFAULT_DECMAKER_CONFIDENCE_THRESHOLD_BUY,
            "confidence_threshold_sell": DEFAULT_DECMAKER_CONFIDENCE_THRESHOLD_SELL,
            "max_percent_higher_price_buy": DEFAULT_DECMAKER_MAX_PERCENT_HIGHER_PRICE_BUY,
            "max_percent_lower_price_sell": DEFAULT_DECMAKER_MAX_PERCENT_LOWER_PRICE_SELL,
        },
    }
