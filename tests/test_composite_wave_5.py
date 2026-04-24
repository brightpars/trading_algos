from __future__ import annotations

import json
from pathlib import Path

import pytest

from trading_algos.alertgen import create_alertgen_algorithm
from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config
from trading_algos.algorithmspec import get_performance_smoke_case


COMPOSITE_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "composite"


def _load_composite_fixture_rows(name: str) -> list[dict[str, object]]:
    return json.loads((COMPOSITE_FIXTURES_ROOT / name).read_text(encoding="utf-8"))


def test_composite_wave_5_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "rl_allocation_controller": (
            "combination:11",
            "reinforcement_learning",
            "rl",
            "portfolio",
            "rl_environment",
        ),
        "hierarchical_controller_meta_policy": (
            "combination:12",
            "reinforcement_learning",
            "hierarchical",
            "portfolio",
            "rl_environment",
        ),
    }

    for alg_key, (
        catalog_ref,
        family,
        subcategory,
        asset_scope,
        input_domain,
    ) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.asset_scope == asset_scope
        assert spec.input_domains == (input_domain,)


def test_rl_allocation_controller_fixture_behavior_and_contract(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "rl_allocation_controller",
            "alg_param": {
                "rows": rows,
                "min_history": 1,
                "gross_exposure_limit": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert output.metadata["catalog_ref"] == "combination:11"
    assert output.metadata["family"] == "reinforcement_learning"
    assert output.metadata["reporting_mode"] == "allocation_trace"
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "buy"
    assert output.points[0].reason_codes == ("selection_ready",)
    assert output.derived_series["selected_symbols"][0] == ["trend", "value", "carry"]
    assert portfolio.rebalances[0].weights["trend"] == pytest.approx(0.7)
    assert portfolio.rebalances[1].weights["carry"] == pytest.approx(0.6)
    assert portfolio.rebalances[1].diagnostics["aggregation_method"] == (
        "rl_allocation_controller"
    )
    assert portfolio.rebalances[1].diagnostics["environment_contract"] == {
        "state_key_count": 3,
        "action_key_count": 5,
    }
    assert payload_name == "rl_report_rl_allocation_controller_PORTFOLIO"
    assert payload["portfolio"]["metadata"]["catalog_ref"] == "combination:11"
    assert payload["data"]["summary_metrics"]["rebalance_count"] == 2


def test_hierarchical_controller_meta_policy_fixture_behavior_and_contract(
    tmp_path: Path,
) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "hierarchical_controller_meta_policy",
            "alg_param": {
                "rows": rows,
                "min_history": 1,
                "gross_exposure_limit": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()

    assert output.metadata["catalog_ref"] == "combination:12"
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "buy"
    assert portfolio.rebalances[0].diagnostics["preferred_family"] == "trend_family"
    assert (
        portfolio.rebalances[0].diagnostics["raw_action_key"]
        == "trend_family_aggressive"
    )
    assert (
        portfolio.rebalances[1].diagnostics["raw_action_key"]
        == "trend_family_defensive"
    )
    assert portfolio.rebalances[1].weights["carry"] == pytest.approx(0.6)
    assert portfolio.rebalances[1].diagnostics["aggregation_method"] == (
        "hierarchical_controller_meta_policy"
    )


def test_composite_wave_5_warmup_and_validation_behaviors(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "rl_allocation_controller",
            "alg_param": {
                "rows": rows,
                "min_history": 2,
                "gross_exposure_limit": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()
    assert output.points[0].signal_label == "neutral"
    assert output.points[0].reason_codes == ("warmup_pending",)
    assert portfolio.rebalances[0].weights == {}
    assert portfolio.rebalances[0].diagnostics["environment_contract"] == {
        "state_key_count": 3,
        "action_key_count": 5,
    }

    with pytest.raises(ValueError, match="gross_exposure_limit must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "rl_allocation_controller",
                "alg_param": {
                    "rows": rows,
                    "min_history": 1,
                    "gross_exposure_limit": 0.0,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="action_aliases must be a dict"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "hierarchical_controller_meta_policy",
                "alg_param": {
                    "rows": rows,
                    "min_history": 1,
                    "gross_exposure_limit": 1.0,
                    "action_aliases": [],
                },
                "buy": True,
                "sell": False,
            }
        )


def test_composite_wave_5_performance_smoke_mapping() -> None:
    assert get_performance_smoke_case("combination:11").performance_budget_id == (
        "perf.execution_engine_v1"
    )
    assert get_performance_smoke_case("combination:12").fixture_ids == (
        "fixture.composite_rl_policy_stub_v1",
    )
