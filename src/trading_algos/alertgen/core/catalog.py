from trading_algos.alertgen.algorithms.composite.catalog import (
    register_composite_alert_algorithms,
)
from trading_algos.alertgen.algorithms.momentum.catalog import (
    register_momentum_alert_algorithms,
)
from trading_algos.alertgen.algorithms.mean_reversion.catalog import (
    register_mean_reversion_alert_algorithms,
)
from trading_algos.alertgen.algorithms.trend.catalog import (
    register_trend_alert_algorithms,
)


_REGISTERED = False


def register_builtin_alert_algorithms():
    global _REGISTERED
    if _REGISTERED:
        return
    register_trend_alert_algorithms()
    register_momentum_alert_algorithms()
    register_mean_reversion_alert_algorithms()
    register_composite_alert_algorithms()
    _REGISTERED = True
