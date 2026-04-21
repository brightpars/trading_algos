from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms
from trading_algos.configuration.serialization import configuration_from_dict
from trading_algos.configuration.validation import validate_configuration_payload


def create_alertgen_algorithm(sensor_config, report_base_path):
    register_builtin_alert_algorithms()
    if sensor_config.get("configuration_payload") is not None:
        configuration = validate_configuration_payload(
            configuration_from_dict(sensor_config["configuration_payload"])
            if isinstance(sensor_config["configuration_payload"], dict)
            else sensor_config["configuration_payload"]
        )
        from trading_algos.alertgen.algorithms.aggregate import (
            ConfigBackedAlertAlgorithm,
        )

        algorithm = ConfigBackedAlertAlgorithm(
            symbol=sensor_config["symbol"],
            report_base_path=report_base_path,
            configuration=configuration,
        )
        return algorithm, configuration.to_dict()
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
