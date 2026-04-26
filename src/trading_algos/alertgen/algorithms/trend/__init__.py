from trading_algos.alertgen.algorithms.trend.boundary_breakout import (
    BoundaryBreakoutAlertAlgorithm,
    DoubleRedConfirmationAlertAlgorithm,
    LowAnchoredBoundaryBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.catalog import (
    register_trend_alert_algorithms,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout import (
    CloseHighChannelBreakoutAlertAlgorithm,
    RollingChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.exponential_moving_average_crossover import (
    ExponentialMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_ribbon_trend import (
    MovingAverageRibbonTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.price_vs_moving_average import (
    PriceVsMovingAverageAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.simple_moving_average_crossover import (
    SimpleMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.triple_moving_average_crossover import (
    TripleMovingAverageCrossoverAlertAlgorithm,
)

__all__ = [
    "BoundaryBreakoutAlertAlgorithm",
    "CloseHighChannelBreakoutAlertAlgorithm",
    "DoubleRedConfirmationAlertAlgorithm",
    "ExponentialMovingAverageCrossoverAlertAlgorithm",
    "LowAnchoredBoundaryBreakoutAlertAlgorithm",
    "MovingAverageRibbonTrendAlertAlgorithm",
    "PriceVsMovingAverageAlertAlgorithm",
    "RollingChannelBreakoutAlertAlgorithm",
    "SimpleMovingAverageCrossoverAlertAlgorithm",
    "TripleMovingAverageCrossoverAlertAlgorithm",
    "register_trend_alert_algorithms",
]
