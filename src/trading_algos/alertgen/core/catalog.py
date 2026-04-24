from trading_algos.alertgen.algorithms.composite.catalog import (
    register_composite_alert_algorithms,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.catalog import (
    register_cross_asset_macro_carry_alert_algorithms,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.catalog import (
    register_factor_risk_premia_alert_algorithms,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.catalog import (
    register_fundamental_ml_composite_alert_algorithms,
)
from trading_algos.alertgen.algorithms.momentum.catalog import (
    register_momentum_alert_algorithms,
)
from trading_algos.alertgen.algorithms.pattern_price_action.catalog import (
    register_pattern_price_action_alert_algorithms,
)
from trading_algos.alertgen.algorithms.mean_reversion.catalog import (
    register_mean_reversion_alert_algorithms,
)
from trading_algos.alertgen.algorithms.volatility_options.catalog import (
    register_volatility_options_alert_algorithms,
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
    register_factor_risk_premia_alert_algorithms()
    register_fundamental_ml_composite_alert_algorithms()
    register_pattern_price_action_alert_algorithms()
    register_mean_reversion_alert_algorithms()
    register_volatility_options_alert_algorithms()
    register_cross_asset_macro_carry_alert_algorithms()
    register_composite_alert_algorithms()
    _REGISTERED = True
