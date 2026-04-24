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
    assert output.derived_series["top_symbol"] == ["AAA", "BBB"]
    assert output.derived_series["selected_symbols"][-1] == ["BBB", "AAA"]
    assert portfolio_output.rebalances[-1].ranking[0].symbol == "BBB"
    assert set(portfolio_output.rebalances[-1].selected_symbols) == {"AAA", "BBB"}
    assert child_output.diagnostics["selection_reason"] == "selection_ready"
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
    assert set(latest_weights) == {"trend", "carry", "value"}
    assert latest_weights["carry"] > latest_weights["trend"] > latest_weights["value"]
    assert sum(abs(weight) for weight in latest_weights.values()) == pytest.approx(1.0)
    assert latest_risk_contributions["carry"] > latest_risk_contributions["trend"]
    assert latest_risk_contributions["value"] < latest_risk_contributions["trend"]


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
    assert latest_rebalance.selected_symbols == ("portfolio",)
    assert 0.0 < latest_rebalance.weights["portfolio"] <= 1.0
    assert latest_rebalance.diagnostics["realized_volatility"] > 0.0
    assert latest_rebalance.diagnostics["applied_leverage"] > 0.0


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
