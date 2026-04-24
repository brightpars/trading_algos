from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.momentum.cross_sectional_momentum import (
    CrossSectionalMomentumAlertAlgorithm,
)


def build_relative_strength_momentum_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    **_kwargs: Any,
) -> CrossSectionalMomentumAlertAlgorithm:
    return CrossSectionalMomentumAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="relative_strength_momentum",
        subcategory="relative",
        rows=list(alg_param["rows"]),
        params=alg_param,
    )
