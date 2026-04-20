from trading_algos.alertgen.core.algorithm_registry import list_alert_algorithm_specs
from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms


def get_default_alertgen_sensor_config(name="sensor_0", *, symbol="SYMBOL"):
    register_builtin_alert_algorithms()
    default_spec = next(
        spec
        for spec in list_alert_algorithm_specs()
        if spec.key == "aggregate_boundary_and_channel"
    )
    return {
        "name": name,
        "sensor_config": {
            "alg_key": default_spec.key,
            "alg_param": default_spec.default_param,
            "symbol": symbol,
            "buy": True,
            "sell": False,
        },
        "enable": True,
    }
