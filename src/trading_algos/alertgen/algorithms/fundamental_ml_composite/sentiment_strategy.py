from __future__ import annotations

from trading_algos.alertgen.algorithms.fundamental_ml_composite.model_helpers import (
    build_fundamental_model_algorithm,
)


def build_sentiment_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_fundamental_model_algorithm(
        algorithm_key="sentiment_strategy",
        symbol=symbol,
        alg_name="sentiment_strategy",
        subcategory="sentiment",
        alg_param=alg_param,
        factor_name="sentiment",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
        catalog_ref="algorithm:89",
        field_weights=alg_param.get("field_weights"),
        threshold=(
            float(alg_param["sentiment_threshold"])
            if "sentiment_threshold" in alg_param
            else None
        ),
        extra_diagnostics={"signal_source": "sentiment_features"},
    )
