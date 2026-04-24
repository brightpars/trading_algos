from __future__ import annotations

from dataclasses import dataclass, field
from inspect import getsourcefile
from pathlib import Path
from typing import Any, Callable, Literal


Normalizer = Callable[[Any, str], Any]
AlgorithmBuilder = Callable[..., Any]
AlgorithmStatus = Literal["draft", "beta", "stable"]
RuntimeKind = Literal["batch_series", "streaming", "execution"]
AssetScope = Literal["single_asset", "pair", "basket", "universe", "portfolio"]
InputDomain = Literal[
    "ohlcv",
    "single_asset_ohlcv",
    "multi_asset_ohlcv",
    "multi_asset_panel",
    "cross_asset_panel",
    "feature_matrix",
    "label_stream",
    "market_calendar",
    "event_calendar",
    "order_book",
    "options",
    "fundamental",
    "fundamentals_pti",
    "events",
]
OutputMode = Literal[
    "signal",
    "score",
    "confidence",
    "model_diagnostics",
    "events",
    "calendar_window",
    "event_window_signal",
    "ranking",
    "selection",
    "weights",
    "diagnostics",
    "child_contributions",
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
    catalog_ref: str
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

    @property
    def builder_name(self) -> str:
        return getattr(self.builder, "__name__", "")

    @property
    def builder_module(self) -> str:
        return str(getattr(self.builder, "__module__", ""))

    @property
    def builder_source_file(self) -> str:
        source_file = getsourcefile(self.builder)
        if source_file is None:
            return ""
        source_path = Path(source_file).resolve()
        project_root = Path(__file__).resolve().parents[3]
        try:
            return str(source_path.relative_to(project_root))
        except ValueError:
            return str(source_path)


AlertAlgorithmSpec = AlgorithmSpec
