from trading_algos.alertgen.algorithms.composite.aggregate import (
    AggregateAlertAlgorithm,
    ConfigBackedAlertAlgorithm,
    agreegate_algs,
)
from trading_algos.alertgen.algorithms.composite.catalog import (
    register_composite_alert_algorithms,
)

__all__ = [
    "AggregateAlertAlgorithm",
    "ConfigBackedAlertAlgorithm",
    "agreegate_algs",
    "register_composite_alert_algorithms",
]
