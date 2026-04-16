from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms


def create_alertgen_algorithm(sensor_config, report_base_path):
    register_builtin_alert_algorithms()
    symbol = sensor_config["symbol"]
    alg_param_for_logging = sensor_config["alg_param"]

    spec = get_alert_algorithm_spec_by_key(sensor_config["alg_key"])
    alg_inst = spec.builder(
        symbol=symbol,
        report_base_path=report_base_path,
        alg_param=sensor_config["alg_param"],
        sensor_config=sensor_config,
    )

    return alg_inst, alg_param_for_logging
