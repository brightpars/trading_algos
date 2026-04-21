from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from typing import cast

import pytest

from trading_algos.configuration.compatibility import (
    evaluate_configuration_compatibility,
)
from trading_algos.configuration.executor import (
    _composite_result,
    evaluate_configuration_graph,
    run_configuration_graph,
)
from trading_algos.configuration.models import AlgorithmConfiguration
from trading_algos.configuration.models import CompositeNode
from trading_algos.configuration.serialization import (
    configuration_from_dict,
    configuration_to_dict,
)
from trading_algos.configuration.validation import validate_configuration_payload


def _sample_rows(count: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "ts": f"2025-01-01 10:00:0{index}",
            "Open": 10 + index,
            "High": 11 + index,
            "Low": 9 + index,
            "Close": 10.5 + index,
        }
        for index in range(count)
    ]


def _algorithm_node(
    node_id: str,
    *,
    alg_key: str = "close_high_channel_breakout",
    alg_param: dict[str, object] | None = None,
    buy_enabled: bool = True,
    sell_enabled: bool = True,
    runtime_editable_param_keys: list[str] | None = None,
) -> dict[str, object]:
    return {
        "node_id": node_id,
        "node_type": "algorithm",
        "name": node_id,
        "alg_key": alg_key,
        "alg_param": alg_param or {"window": 2},
        "buy_enabled": buy_enabled,
        "sell_enabled": sell_enabled,
        "runtime_editable_param_keys": runtime_editable_param_keys or [],
    }


def _configuration_payload(
    *,
    root_node_id: str = "alg-a",
    nodes: list[dict[str, object]] | None = None,
    compatibility_metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "config_key": "sample-config",
        "version": "1.2.3",
        "name": "Sample Config",
        "description": "example",
        "tags": ["example", "test"],
        "notes": "notes",
        "status": "draft",
        "root_node_id": root_node_id,
        "nodes": nodes or [_algorithm_node("alg-a")],
        "runtime_overrides": {},
        "algorithm_package_constraints": {},
        "compatibility_metadata": compatibility_metadata or {},
        "created_by": "tester",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


def test_configuration_round_trip_preserves_graph_metadata() -> None:
    payload = _configuration_payload(
        root_node_id="group-1",
        nodes=[
            _algorithm_node("alg-a"),
            _algorithm_node("alg-b", alg_param={"window": 3}),
            {
                "node_id": "group-1",
                "node_type": "and",
                "name": "AND Group",
                "children": ["alg-a", "alg-b"],
            },
        ],
        compatibility_metadata={
            "expected_package_name": "trading_algos",
            "minimum_supported_version": "0.1.0",
            "compatibility_state": "compatible",
            "compatibility_messages": ["ok"],
        },
    )

    configuration = configuration_from_dict(payload)
    round_tripped = configuration_to_dict(configuration)

    assert isinstance(configuration, AlgorithmConfiguration)
    assert round_tripped["config_key"] == payload["config_key"]
    assert round_tripped["root_node_id"] == payload["root_node_id"]
    assert list(cast(Sequence[str], round_tripped["tags"])) == payload["tags"]
    assert round_tripped["created_at"] == payload["created_at"]
    assert len(cast(Sequence[object], round_tripped["nodes"])) == 3


@pytest.mark.parametrize(
    "payload",
    [
        _configuration_payload(),
        _configuration_payload(
            root_node_id="group-1",
            nodes=[
                _algorithm_node("alg-a"),
                _algorithm_node("alg-b", alg_param={"window": 3}),
                {
                    "node_id": "group-1",
                    "node_type": "and",
                    "children": ["alg-a", "alg-b"],
                },
            ],
        ),
        _configuration_payload(
            root_node_id="pipe-1",
            nodes=[
                _algorithm_node("alg-a"),
                _algorithm_node("alg-b", alg_param={"window": 3}),
                {
                    "node_id": "pipe-1",
                    "node_type": "pipeline",
                    "children": ["alg-a", "alg-b"],
                },
            ],
        ),
    ],
)
def test_validate_configuration_payload_accepts_valid_graphs(
    payload: dict[str, object],
) -> None:
    configuration = validate_configuration_payload(payload)

    assert configuration.config_key == "sample-config"


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda payload: payload.pop("config_key"), "config_key is required"),
        (lambda payload: payload.pop("version"), "version is required"),
        (lambda payload: payload.pop("name"), "name is required"),
        (lambda payload: payload.pop("root_node_id"), "root_node_id is required"),
        (
            lambda payload: payload.update({"nodes": []}),
            "nodes must be a non-empty list",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [_algorithm_node("dup"), _algorithm_node("dup")],
                    "root_node_id": "dup",
                }
            ),
            "must be unique",
        ),
        (
            lambda payload: payload.update({"root_node_id": "missing-root"}),
            "must reference an existing node",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        _algorithm_node("alg-a"),
                        {
                            "node_id": "group-1",
                            "node_type": "and",
                            "children": ["alg-a", "missing-child"],
                        },
                    ],
                    "root_node_id": "group-1",
                }
            ),
            "references missing child node",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        {
                            "node_id": "loop-a",
                            "node_type": "and",
                            "children": ["loop-b", "alg-a"],
                        },
                        {
                            "node_id": "loop-b",
                            "node_type": "or",
                            "children": ["loop-a", "alg-a"],
                        },
                        _algorithm_node("alg-a"),
                    ],
                    "root_node_id": "loop-a",
                }
            ),
            "must be acyclic",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        {
                            "node_id": "bad",
                            "node_type": "weighted_vote",
                        }
                    ],
                    "root_node_id": "bad",
                }
            ),
            "unsupported node_type",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        {
                            **_algorithm_node("alg-a"),
                            "children": ["alg-b"],
                        }
                    ]
                }
            ),
            "must not declare children",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        _algorithm_node("alg-a"),
                        {
                            "node_id": "group-1",
                            "node_type": "and",
                            "children": ["alg-a"],
                        },
                    ],
                    "root_node_id": "group-1",
                }
            ),
            "requires at least 2 children",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        _algorithm_node(
                            "alg-a",
                            buy_enabled=False,
                            sell_enabled=False,
                        )
                    ]
                }
            ),
            "requires at least one of buy_enabled/sell_enabled",
        ),
        (
            lambda payload: payload.update(
                {"nodes": [_algorithm_node("alg-a", alg_key="not-real")]}
            ),
            "unsupported",
        ),
        (
            lambda payload: payload.update(
                {"nodes": [_algorithm_node("alg-a", alg_param={"window": 0})]}
            ),
            "must be > 0",
        ),
        (
            lambda payload: payload.update(
                {
                    "nodes": [
                        _algorithm_node(
                            "alg-a",
                            runtime_editable_param_keys=["missing_key"],
                        )
                    ]
                }
            ),
            "runtime_editable_param_keys",
        ),
    ],
)
def test_validate_configuration_payload_rejects_invalid_graphs(
    mutator: Any,
    message: str,
) -> None:
    payload = _configuration_payload()
    mutator(payload)

    with pytest.raises(ValueError, match=message):
        validate_configuration_payload(payload)


def test_configuration_compatibility_classifies_version_and_algorithm_issues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _configuration_payload(
        compatibility_metadata={
            "expected_package_version": "9.9.9",
            "minimum_supported_version": "0.0.1",
            "maximum_supported_version": "1.5.0",
        }
    )
    configuration = configuration_from_dict(payload)
    monkeypatch.setattr(
        "trading_algos.configuration.compatibility._installed_package_version",
        lambda: "1.2.0",
    )

    compatibility = evaluate_configuration_compatibility(configuration)

    assert compatibility.compatibility_state == "warning"
    assert compatibility.algorithm_refs == ("close_high_channel_breakout",)
    assert any(
        "expected package version 9.9.9" in item
        for item in compatibility.compatibility_messages
    )


def test_configuration_compatibility_rejects_missing_algorithm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = configuration_from_dict(
        _configuration_payload(nodes=[_algorithm_node("alg-a", alg_key="missing")])
    )
    monkeypatch.setattr(
        "trading_algos.configuration.compatibility._installed_package_version",
        lambda: "1.2.0",
    )

    compatibility = evaluate_configuration_compatibility(configuration)

    assert compatibility.compatibility_state == "incompatible"
    assert any("not available" in item for item in compatibility.compatibility_messages)


def test_configuration_compatibility_uses_numeric_version_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = configuration_from_dict(
        _configuration_payload(
            compatibility_metadata={
                "minimum_supported_version": "1.2.0",
                "maximum_supported_version": "1.11.0",
            }
        )
    )
    monkeypatch.setattr(
        "trading_algos.configuration.compatibility._installed_package_version",
        lambda: "1.10.0",
    )

    compatibility = evaluate_configuration_compatibility(configuration)

    assert compatibility.compatibility_state == "compatible"
    assert compatibility.compatibility_messages == ()


def test_run_configuration_graph_executes_algorithm_root() -> None:
    execution = run_configuration_graph(
        configuration=_configuration_payload(),
        symbol="AAPL",
        report_base_path="/tmp",
        candles=_sample_rows(),
    )

    root_result = execution["root_result"]
    assert execution["configuration"].config_key == "sample-config"
    assert root_result["node_id"] == "alg-a"
    assert len(root_result["rows"]) == 5
    assert len(execution["node_results"]) == 1


def test_run_configuration_graph_supports_deterministic_and_or_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decisions_by_node = {
        "alg-a": [
            {
                "buy_signal": True,
                "sell_signal": False,
                "no_signal": False,
                "confidence": 0.6,
            },
            {
                "buy_signal": False,
                "sell_signal": True,
                "no_signal": False,
                "confidence": 0.3,
            },
        ],
        "alg-b": [
            {
                "buy_signal": True,
                "sell_signal": False,
                "no_signal": False,
                "confidence": 0.9,
            },
            {
                "buy_signal": False,
                "sell_signal": False,
                "no_signal": True,
                "confidence": 0.2,
            },
        ],
    }

    def fake_algorithm_result(node: Any, **_: Any) -> dict[str, Any]:
        decisions = decisions_by_node[node.node_id]
        rows = []
        for index, decision in enumerate(decisions):
            row = _sample_rows(2)[index]
            rows.append(
                {
                    **row,
                    "buy_SIGNAL": decision["buy_signal"],
                    "sell_SIGNAL": decision["sell_signal"],
                    "no_SIGNAL": decision["no_signal"],
                    "trend_confidence": decision["confidence"],
                }
            )
        return {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "node_name": node.name,
            "alg_key": node.alg_key,
            "alg_param": node.alg_param,
            "algorithm": object(),
            "rows": rows,
            "decisions": decisions,
            "chart_payload": {},
            "latest_decision": decisions[-1],
            "eval_dict": {},
        }

    monkeypatch.setattr(
        "trading_algos.configuration.executor._algorithm_result",
        fake_algorithm_result,
    )

    and_execution = run_configuration_graph(
        configuration=_configuration_payload(
            root_node_id="and-1",
            nodes=[
                _algorithm_node("alg-a"),
                _algorithm_node("alg-b"),
                {
                    "node_id": "and-1",
                    "node_type": "and",
                    "children": ["alg-a", "alg-b"],
                },
            ],
        ),
        symbol="AAPL",
        report_base_path="/tmp",
        candles=_sample_rows(2),
    )
    or_execution = run_configuration_graph(
        configuration=_configuration_payload(
            root_node_id="or-1",
            nodes=[
                _algorithm_node("alg-a"),
                _algorithm_node("alg-b"),
                {
                    "node_id": "or-1",
                    "node_type": "or",
                    "children": ["alg-a", "alg-b"],
                },
            ],
        ),
        symbol="AAPL",
        report_base_path="/tmp",
        candles=_sample_rows(2),
    )

    assert and_execution["root_result"]["decisions"] == [
        {
            "buy_signal": True,
            "sell_signal": False,
            "no_signal": False,
            "confidence": 0.6,
        },
        {
            "buy_signal": False,
            "sell_signal": False,
            "no_signal": True,
            "confidence": 0.2,
        },
    ]
    assert or_execution["root_result"]["decisions"] == [
        {
            "buy_signal": True,
            "sell_signal": False,
            "no_signal": False,
            "confidence": 0.9,
        },
        {
            "buy_signal": False,
            "sell_signal": True,
            "no_signal": False,
            "confidence": 0.3,
        },
    ]


def test_run_configuration_graph_rejects_pipeline_execution() -> None:
    with pytest.raises(
        ValueError, match="pipeline node execution is not implemented yet"
    ):
        run_configuration_graph(
            configuration=_configuration_payload(
                root_node_id="pipe-1",
                nodes=[
                    _algorithm_node("alg-a"),
                    _algorithm_node("alg-b"),
                    {
                        "node_id": "pipe-1",
                        "node_type": "pipeline",
                        "children": ["alg-a", "alg-b"],
                    },
                ],
            ),
            symbol="AAPL",
            report_base_path="/tmp",
            candles=_sample_rows(2),
        )


def test_evaluate_configuration_graph_reports_signal_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_result = {
        "node_id": "alg-a",
        "decisions": [
            {
                "buy_signal": True,
                "sell_signal": False,
                "no_signal": False,
                "confidence": 0.5,
            },
            {
                "buy_signal": False,
                "sell_signal": True,
                "no_signal": False,
                "confidence": 0.2,
            },
            {
                "buy_signal": False,
                "sell_signal": False,
                "no_signal": True,
                "confidence": 0.0,
            },
        ],
    }
    monkeypatch.setattr(
        "trading_algos.configuration.executor.run_configuration_graph",
        lambda **_: {
            "configuration": configuration_from_dict(_configuration_payload()),
            "root_result": root_result,
            "node_results": [root_result],
        },
    )

    evaluation = evaluate_configuration_graph(
        configuration=_configuration_payload(),
        symbol="AAPL",
        report_base_path="/tmp",
        candles=_sample_rows(3),
    )

    assert evaluation["signal_summary"] == {
        "buy_count": 1,
        "sell_count": 1,
        "no_signal_count": 1,
        "total_rows": 3,
    }


def test_composite_result_uses_min_for_and_and_max_for_or() -> None:
    child_results = [
        {
            "node_id": "a",
            "decisions": [
                {
                    "buy_signal": True,
                    "sell_signal": False,
                    "no_signal": False,
                    "confidence": 0.4,
                }
            ],
        },
        {
            "node_id": "b",
            "decisions": [
                {
                    "buy_signal": True,
                    "sell_signal": False,
                    "no_signal": False,
                    "confidence": 0.9,
                }
            ],
        },
    ]

    and_configuration = configuration_from_dict(
        _configuration_payload(
            root_node_id="and-1",
            nodes=[
                _algorithm_node("alg-a"),
                _algorithm_node("alg-b"),
                {
                    "node_id": "and-1",
                    "node_type": "and",
                    "children": ["alg-a", "alg-b"],
                },
            ],
        )
    )
    and_node = cast(CompositeNode, and_configuration.nodes[2])
    and_result = _composite_result(
        and_node,
        child_results,
        candles=_sample_rows(1),
    )
    or_configuration = configuration_from_dict(
        _configuration_payload(
            root_node_id="or-1",
            nodes=[
                _algorithm_node("alg-a"),
                _algorithm_node("alg-b"),
                {"node_id": "or-1", "node_type": "or", "children": ["alg-a", "alg-b"]},
            ],
        )
    )
    or_node = cast(CompositeNode, or_configuration.nodes[2])
    or_result = _composite_result(
        or_node,
        child_results,
        candles=_sample_rows(1),
    )

    assert and_result["decisions"][0]["confidence"] == 0.4
    assert or_result["decisions"][0]["confidence"] == 0.9
