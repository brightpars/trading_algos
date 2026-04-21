from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


NodeType = Literal["algorithm", "and", "or", "pipeline"]
CompatibilityState = Literal["compatible", "warning", "incompatible"]


@dataclass(frozen=True)
class CompatibilityMetadata:
    expected_package_name: str = "trading_algos"
    expected_package_version: str | None = None
    minimum_supported_version: str | None = None
    maximum_supported_version: str | None = None
    algorithm_refs: tuple[str, ...] = ()
    compatibility_state: CompatibilityState = "compatible"
    compatibility_messages: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BaseNode:
    node_id: str
    node_type: NodeType
    name: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AlgorithmNode(BaseNode):
    alg_key: str = ""
    alg_param: dict[str, object] = field(default_factory=dict)
    buy_enabled: bool = True
    sell_enabled: bool = True
    runtime_editable_param_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompositeNode(BaseNode):
    children: tuple[str, ...] = ()


@dataclass(frozen=True)
class PipelineNode(CompositeNode):
    stage_policy: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AlgorithmConfiguration:
    config_key: str
    version: str
    name: str
    description: str = ""
    tags: tuple[str, ...] = ()
    notes: str = ""
    status: str = "draft"
    root_node_id: str = ""
    nodes: tuple[BaseNode, ...] = ()
    runtime_overrides: dict[str, object] = field(default_factory=dict)
    algorithm_package_constraints: dict[str, object] = field(default_factory=dict)
    compatibility_metadata: CompatibilityMetadata = field(
        default_factory=CompatibilityMetadata
    )
    created_by: str = ""
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["nodes"] = [node.to_dict() for node in self.nodes]
        payload["compatibility_metadata"] = self.compatibility_metadata.to_dict()
        return payload
