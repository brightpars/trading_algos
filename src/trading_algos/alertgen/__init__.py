from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
    list_alert_algorithm_specs,
)
from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms
from trading_algos.alertgen.contracts import AlertAlgorithmOutput, AlertSeriesPoint
from trading_algos.alertgen.core.factory import create_alertgen_algorithm
from trading_algos.alertgen.engine_core import AlertgenAlgorithmCore


register_builtin_alert_algorithms()

__all__ = [
    "list_alert_algorithm_specs",
    "get_alert_algorithm_spec_by_key",
    "create_alertgen_algorithm",
    "AlertgenAlgorithmCore",
    "AlertAlgorithmOutput",
    "AlertSeriesPoint",
]
