from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal


Normalizer = Callable[[Any, str], Any]
AlgorithmBuilder = Callable[..., Any]
AlgorithmStatus = Literal["draft", "beta", "stable"]
RuntimeKind = Literal["batch_series", "streaming", "execution"]
AssetScope = Literal["single_asset", "pair", "basket", "universe"]
InputDomain = Literal[
    "ohlcv",
    "multi_asset_ohlcv",
    "order_book",
    "options",
    "fundamental",
    "events",
]
OutputMode = Literal[
    "signal",
    "score",
    "confidence",
    "events",
    "ranking",
    "regime",
    "execution_plan",
]
CompositionRole = Literal[
    "leaf_signal",
    "filter",
    "regime_gate",
    "ensemble_member",
    "execution_only",
]


@dataclass(frozen=True)
class AlgorithmSpec:
    key: str
    name: str
    builder: AlgorithmBuilder
    default_param: Any
    param_normalizer: Normalizer
    description: str = ""
    param_schema: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    supports_buy: bool = True
    supports_sell: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)
    version: str = "1.0"
    category: str = "general"
    family: str = "general"
    subcategory: str = ""
    status: AlgorithmStatus = "stable"
    warmup_period: int = 1
    input_domains: tuple[InputDomain, ...] = ("ohlcv",)
    asset_scope: AssetScope = "single_asset"
    output_modes: tuple[OutputMode, ...] = ("signal", "confidence")
    runtime_kind: RuntimeKind = "batch_series"
    composition_roles: tuple[CompositionRole, ...] = (
        "leaf_signal",
        "ensemble_member",
    )


AlertAlgorithmSpec = AlgorithmSpec
