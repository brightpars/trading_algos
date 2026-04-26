from __future__ import annotations

import json
from pathlib import Path

import pytest

from trading_algos.alertgen import create_alertgen_algorithm
from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config


COMPOSITE_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "composite"


def _load_composite_fixture_rows(name: str) -> list[dict[str, object]]:
    return json.loads((COMPOSITE_FIXTURES_ROOT / name).read_text(encoding="utf-8"))


def test_composite_wave_2_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "rank_aggregation": ("combination:3", "rule_based_combination", "rank"),
        "risk_budgeting_risk_parity": ("combination:5", "risk_overlay", "risk"),
        "volatility_targeting_overlay": (
            "combination:6",
            "risk_overlay",
            "volatility",
        ),
    }

    for alg_key, (catalog_ref, family, subcategory) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.asset_scope == "portfolio"


def test_rank_aggregation_fixture_behavior_and_contract(tmp_path: Path) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "rank_aggregation",
            "alg_param": {
                "rows": _load_composite_fixture_rows("rank_aggregation.json"),
                "aggregation_method": "average_rank",
                "rank_field_names": ["child_rank_1", "child_rank_2"],
                "score_field_names": ["child_score_1"],
                "top_k": 2,
                "minimum_child_count": 1,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]

    assert output.metadata["catalog_ref"] == "combination:3"
    assert output.metadata["family"] == "rule_based_combination"
    assert output.metadata["reporting_mode"] == "composite_trace"
    assert output.metadata["warmup_period"] == 1
    assert output.derived_series["top_symbol"] == ["AAA", "BBB"]
    assert output.derived_series["selected_symbols"][-1] == ["BBB", "AAA"]
    assert output.points[-1].signal_label == "buy"
    assert output.points[-1].reason_codes == ("selection_ready",)
    assert portfolio_output.rebalances[-1].ranking[0].symbol == "BBB"
    assert set(portfolio_output.rebalances[-1].selected_symbols) == {"AAA", "BBB"}
    assert portfolio_output.rebalances[-1].diagnostics["selected_symbols"] == [
        "BBB",
        "AAA",
    ]
    assert child_output.diagnostics["selection_reason"] == "selection_ready"
    assert child_output.diagnostics["selected_symbols"] == ["BBB", "AAA"]
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


def test_risk_budgeting_fixture_behavior_and_contract(tmp_path: Path) -> None:
    fixture_rows = _load_composite_fixture_rows("risk_budget.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "risk_budgeting_risk_parity",
            "alg_param": {
                "rows": fixture_rows,
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    latest_weights = portfolio_output.rebalances[-1].weights
    latest_risk_contributions = portfolio_output.rebalances[-1].diagnostics[
        "risk_contributions"
    ]

    assert output.metadata["catalog_ref"] == "combination:5"
    assert output.metadata["family"] == "risk_overlay"
    assert output.metadata["reporting_mode"] == "allocation_trace"
    assert output.points[-1].signal_label == "buy"
    assert output.points[-1].reason_codes == ("selection_ready",)
    assert set(latest_weights) == {"trend", "carry", "value"}
    assert latest_weights["carry"] > latest_weights["trend"] > latest_weights["value"]
    assert sum(abs(weight) for weight in latest_weights.values()) == pytest.approx(1.0)
    assert latest_risk_contributions["carry"] > latest_risk_contributions["trend"]
    assert latest_risk_contributions["value"] < latest_risk_contributions["trend"]
    assert portfolio_output.rebalances[-1].diagnostics["selected_symbols"] == [
        "carry",
        "trend",
        "value",
    ]


def test_volatility_targeting_fixture_behavior_and_contract(tmp_path: Path) -> None:
    fixture_rows = _load_composite_fixture_rows("risk_budget.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "volatility_targeting_overlay",
            "alg_param": {
                "rows": fixture_rows,
                "target_volatility": 0.01,
                "base_weight": 1.0,
                "min_history": 3,
                "max_leverage": 2.0,
                "min_leverage": 0.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    latest_rebalance = portfolio_output.rebalances[-1]

    assert output.metadata["catalog_ref"] == "combination:6"
    assert output.metadata["family"] == "risk_overlay"
    assert output.metadata["reporting_mode"] == "allocation_trace"
    assert output.points[-1].signal_label == "buy"
    assert output.points[-1].reason_codes == ("selection_ready",)
    assert latest_rebalance.selected_symbols == ("portfolio",)
    assert 0.0 < latest_rebalance.weights["portfolio"] <= 1.0
    assert latest_rebalance.diagnostics["realized_volatility"] > 0.0
    assert latest_rebalance.diagnostics["applied_leverage"] > 0.0
    assert latest_rebalance.diagnostics["selected_symbols"] == ["portfolio"]


def test_composite_wave_2_warmup_behavior_is_neutral_until_history_is_ready(
    tmp_path: Path,
) -> None:
    rank_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "rank_aggregation",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-03-31",
                        "asset_rows": [
                            {"symbol": "AAA", "child_rank_1": 1},
                            {"symbol": "BBB"},
                        ],
                    }
                ],
                "aggregation_method": "average_rank",
                "rank_field_names": ["child_rank_1"],
                "top_k": 2,
                "minimum_child_count": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    rank_output = rank_algorithm.normalized_output()
    rank_portfolio = rank_algorithm.portfolio_output()

    assert rank_output.points[-1].signal_label == "neutral"
    assert rank_output.points[-1].reason_codes == ("warmup_pending",)
    assert rank_output.derived_series["warmup_ready"][-1] is False
    assert rank_portfolio.rebalances[-1].selected_symbols == ()
    assert rank_portfolio.rebalances[-1].diagnostics["missing_symbols"] == (
        "AAA",
        "BBB",
    )

    risk_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "risk_budgeting_risk_parity",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-03-31",
                        "sleeve_returns": {
                            "trend": [0.01, 0.02],
                            "carry": [0.01],
                        },
                    }
                ],
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    risk_output = risk_algorithm.normalized_output()
    risk_portfolio = risk_algorithm.portfolio_output()

    assert risk_output.points[-1].signal_label == "neutral"
    assert risk_output.points[-1].reason_codes == ("warmup_pending",)
    assert risk_output.derived_series["warmup_ready"][-1] is False
    assert risk_portfolio.rebalances[-1].weights == {}
    assert risk_portfolio.rebalances[-1].diagnostics[
        "insufficient_history_sleeves"
    ] == (
        "carry",
        "trend",
    )

    volatility_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "volatility_targeting_overlay",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-03-31",
                        "portfolio_returns": [0.01, 0.02],
                    }
                ],
                "target_volatility": 0.01,
                "base_weight": 1.0,
                "min_history": 3,
                "max_leverage": 2.0,
                "min_leverage": 0.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    volatility_output = volatility_algorithm.normalized_output()
    volatility_portfolio = volatility_algorithm.portfolio_output()

    assert volatility_output.points[-1].signal_label == "neutral"
    assert volatility_output.points[-1].reason_codes == ("warmup_pending",)
    assert volatility_output.derived_series["warmup_ready"][-1] is False
    assert volatility_portfolio.rebalances[-1].selected_symbols == ()
    assert volatility_portfolio.rebalances[-1].diagnostics["selected_symbols"] == []


def test_composite_wave_2_interactive_payloads_and_performance_smoke_mapping(
    tmp_path: Path,
) -> None:
    algorithms = {
        "rank_aggregation": {
            "symbol": "UNIVERSE",
            "alg_param": {
                "rows": _load_composite_fixture_rows("rank_aggregation.json"),
                "aggregation_method": "average_rank",
                "rank_field_names": ["child_rank_1", "child_rank_2"],
                "score_field_names": ["child_score_1"],
                "top_k": 2,
                "minimum_child_count": 1,
            },
            "expected_budget": "perf.cross_sectional_rebalance_v1",
        },
        "risk_budgeting_risk_parity": {
            "symbol": "PORTFOLIO",
            "alg_param": {
                "rows": _load_composite_fixture_rows("risk_budget.json"),
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
            },
            "expected_budget": "perf.cross_sectional_rebalance_v1",
        },
        "volatility_targeting_overlay": {
            "symbol": "PORTFOLIO",
            "alg_param": {
                "rows": _load_composite_fixture_rows("risk_budget.json"),
                "target_volatility": 0.01,
                "base_weight": 1.0,
                "min_history": 3,
                "max_leverage": 2.0,
                "min_leverage": 0.0,
            },
            "expected_budget": "perf.cross_sectional_rebalance_v1",
        },
    }

    for alg_key, case in algorithms.items():
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": case["symbol"],
                "alg_key": alg_key,
                "alg_param": case["alg_param"],
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path),
        )
        payload, payload_name = algorithm.interactive_report_payloads()[0]

        assert payload_name == f"rebalance_report_{alg_key}_{case['symbol']}"
        assert payload["algorithm_key"] == alg_key
        assert (
            payload["data"]["metadata"]["catalog_ref"]
            == payload["portfolio"]["metadata"]["catalog_ref"]
        )

    from trading_algos.algorithmspec import get_performance_smoke_case

    assert (
        get_performance_smoke_case("combination:3").performance_budget_id
        == "perf.cross_sectional_rebalance_v1"
    )
    assert (
        get_performance_smoke_case("combination:5").performance_budget_id
        == "perf.cross_sectional_rebalance_v1"
    )
    assert (
        get_performance_smoke_case("combination:6").performance_budget_id
        == "perf.cross_sectional_rebalance_v1"
    )


def test_composite_wave_2_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="rank_field_names"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "rank_aggregation",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("rank_aggregation.json"),
                    "aggregation_method": "average_rank",
                    "rank_field_names": [],
                    "top_k": 2,
                    "minimum_child_count": 1,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="target_gross_exposure must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "risk_budgeting_risk_parity",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("risk_budget.json"),
                    "rebalance_frequency": "monthly",
                    "target_gross_exposure": 0.0,
                    "min_history": 3,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="requires max_leverage >= min_leverage"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "volatility_targeting_overlay",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("risk_budget.json"),
                    "target_volatility": 0.01,
                    "base_weight": 1.0,
                    "min_history": 3,
                    "max_leverage": 0.5,
                    "min_leverage": 1.0,
                },
                "buy": True,
                "sell": False,
            }
        )
