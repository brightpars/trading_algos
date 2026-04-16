from trading_algos.decmaker.algorithms.alg1 import alg1


def create_decmaker_algorithm(container_obj, engine_config):
    return alg1(
        container_obj=container_obj,
        confidence_threshold_buy=engine_config["confidence_threshold_buy"],
        confidence_threshold_sell=engine_config["confidence_threshold_sell"],
        max_percent_higher_price_buy=engine_config["max_percent_higher_price_buy"],
        max_percent_lower_price_sell=engine_config["max_percent_lower_price_sell"],
    )
