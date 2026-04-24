from __future__ import annotations

from csv import DictReader
from pathlib import Path
from typing import cast

import pytest

from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.factory import create_alertgen_algorithm
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config


EVENT_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "events"


def _load_event_price_rows(name: str) -> list[dict[str, object]]:
    with (EVENT_FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(DictReader(handle))
    return [
        {
            "ts": row["ts"],
            "symbol": row["symbol"],
            "Close": float(row["Close"]),
        }
        for row in rows
    ]


def _earnings_event_rows() -> list[dict[str, object]]:
    return [
        {
            "symbol": "AAA",
            "event_timestamp": "2025-02-03 16:05:00",
            "public_timestamp": "2025-02-03 16:05:00",
            "event_type": "earnings",
            "surprise": 0.15,
            "pre_drift_score": 0.25,
            "premium_score": 0.10,
        }
    ]


def _index_rebalance_event_rows() -> list[dict[str, object]]:
    return [
        {
            "symbol": "AAA",
            "event_timestamp": "2025-03-24 09:30:00",
            "public_timestamp": "2025-03-21 09:30:00",
            "event_type": "index_rebalance",
            "expected_flow": 0.80,
            "expected_direction": "buy",
        }
    ]


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref", "subcategory"),
    [
        ("post_earnings_announcement_drift", "algorithm:117", "earnings"),
        ("pre_earnings_announcement_drift", "algorithm:118", "pre"),
        ("earnings_announcement_premium", "algorithm:119", "earnings"),
        ("index_rebalancing_effect_strategy", "algorithm:120", "index"),
        (
            "etf_rebalancing_anticipation_front_run_strategy",
            "algorithm:121",
            "etf",
        ),
    ],
)
def test_event_wave_1_registration_metadata_matches_manifest_contract(
    alg_key: str, catalog_ref: str, subcategory: str
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)

    assert spec.catalog_ref == catalog_ref
    assert spec.family == "event_driven"
    assert spec.category == "event_driven"
    assert spec.subcategory == subcategory
    assert spec.warmup_period == 1
    assert spec.asset_scope == "single_asset"
    assert spec.output_modes == (
        "event_window_signal",
        "event_metadata",
        "diagnostics",
    )


def test_event_wave_1_after_close_fixture_respects_public_timestamp(
    tmp_path: Path,
) -> None:
    rows = _load_event_price_rows("earnings_after_close.csv")
    event_rows = _earnings_event_rows()

    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "post_earnings_announcement_drift",
            "alg_param": {
                "rows": rows,
                "event_rows": event_rows,
                "event_value_field": "surprise",
                "post_event_window_days": 2,
                "pre_event_window_days": 0,
                "bullish_phase": "post_event",
                "minimum_score_threshold": 0.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert output.points[0].signal_label == "neutral"
    assert output.points[0].reason_codes == ("warmup_pending",)
    assert output.points[1].signal_label == "buy"
    assert output.derived_series["event_window_active"] == [False, True, True, True]
    assert output.derived_series["warmup_ready"] == [False, True, True, True]
    assert output.derived_series["event_window_phase"][-1] == "post_event"
    assert output.derived_series["decision_reason"][0] == "warmup_pending"
    assert output.derived_series["decision_reason"][1] == "post_event_window_active"
    assert child_output.diagnostics["event_anchor_timestamp"] == "2025-02-03 16:05:00"
    assert child_output.diagnostics["surprise"] == pytest.approx(0.15)
    assert child_output.diagnostics["decision_reason"] == "post_event_window_active"
    assert child_output.diagnostics["reporting_mode"] == "event_window"
    assert output.metadata["catalog_ref"] == "algorithm:117"
    assert payload_name.startswith("event_report_post_earnings_announcement_drift_")
    assert payload["report_type"] == "event_window"
    assert payload["metadata"]["catalog_ref"] == "algorithm:117"
    assert payload["summary_metrics"]["active_event_count"] == 3
    assert payload["latest_child_output"]["diagnostics"]["decision_reason"] == (
        "post_event_window_active"
    )


def test_event_wave_1_pre_earnings_window_activates_before_event(
    tmp_path: Path,
) -> None:
    rows = _load_event_price_rows("earnings_after_close.csv")
    event_rows = [
        {
            **_earnings_event_rows()[0],
            "public_timestamp": "2025-02-02 16:05:00",
        }
    ]

    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "pre_earnings_announcement_drift",
            "alg_param": {
                "rows": rows,
                "event_rows": event_rows,
                "event_value_field": "pre_drift_score",
                "pre_event_window_days": 1,
                "post_event_window_days": 0,
                "bullish_phase": "pre_event",
                "minimum_score_threshold": 0.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()

    assert output.points[0].signal_label == "neutral"
    assert output.points[0].reason_codes == ("warmup_pending",)
    assert output.points[1].signal_label == "neutral"
    assert output.derived_series["event_window_phase"][0] == "pre_event"
    assert output.derived_series["event_window_phase"][1] == "post_event"
    assert output.derived_series["decision_reason"][1] == "post_event_phase_filtered"


def test_event_wave_1_rebalance_fixture_only_signals_inside_window(
    tmp_path: Path,
) -> None:
    rows = _load_event_price_rows("index_rebalance.csv")
    event_rows = _index_rebalance_event_rows()

    index_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "index_rebalancing_effect_strategy",
            "alg_param": {
                "rows": rows,
                "event_rows": event_rows,
                "event_value_field": "expected_flow",
                "expected_direction_field": "expected_direction",
                "pre_event_window_days": 2,
                "post_event_window_days": 0,
                "bullish_phase": "pre_event",
                "minimum_score_threshold": 0.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "index"),
    )
    etf_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "etf_rebalancing_anticipation_front_run_strategy",
            "alg_param": {
                "rows": rows,
                "event_rows": event_rows,
                "event_value_field": "expected_flow",
                "expected_direction_field": "expected_direction",
                "pre_event_window_days": 3,
                "post_event_window_days": 0,
                "bullish_phase": "pre_event",
                "minimum_score_threshold": 0.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "etf"),
    )

    index_output = index_algorithm.normalized_output()
    etf_output = etf_algorithm.normalized_output()

    assert [point.signal_label for point in index_output.points] == [
        "neutral",
        "buy",
        "neutral",
        "neutral",
    ]
    assert [point.signal_label for point in etf_output.points] == [
        "neutral",
        "buy",
        "neutral",
        "neutral",
    ]
    assert index_output.points[0].reason_codes == ("warmup_pending",)
    assert True in index_output.derived_series["event_window_active"]
    assert index_output.derived_series["event_window_phase"][1] == "pre_event"
    assert (
        index_output.derived_series["decision_reason"][2] == "post_event_phase_filtered"
    )
    assert (
        etf_output.child_outputs[0].diagnostics["decision_reason"]
        == "no_event_available"
    )
    assert "index_rebalance" in [
        point.diagnostics.get("event_type") for point in etf_output.points
    ]


def test_event_wave_1_short_history_reports_warmup_pending(tmp_path: Path) -> None:
    rows = _load_event_price_rows("earnings_after_close.csv")[:1]

    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "post_earnings_announcement_drift",
            "alg_param": {
                "rows": rows,
                "event_rows": _earnings_event_rows(),
                "event_value_field": "surprise",
                "post_event_window_days": 2,
                "bullish_phase": "post_event",
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()

    assert all(point.signal_label == "neutral" for point in output.points)
    assert all(point.reason_codes == ("warmup_pending",) for point in output.points)
    assert output.derived_series["warmup_ready"] == [False]
    assert output.derived_series["decision_reason"] == ["warmup_pending"]
    assert output.child_outputs[0].reason_codes == ("warmup_pending",)
    assert output.child_outputs[0].diagnostics["warmup_ready"] is False
    assert output.child_outputs[0].diagnostics["decision_reason"] == "warmup_pending"


def test_event_wave_1_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="missing required keys: event_value_field"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAA",
                "alg_key": "post_earnings_announcement_drift",
                "alg_param": {
                    "rows": _load_event_price_rows("earnings_after_close.csv"),
                    "event_rows": _earnings_event_rows(),
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="pre_event_window_days must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAA",
                "alg_key": "pre_earnings_announcement_drift",
                "alg_param": {
                    "rows": _load_event_price_rows("earnings_after_close.csv"),
                    "event_rows": _earnings_event_rows(),
                    "event_value_field": "pre_drift_score",
                    "pre_event_window_days": -1,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="bullish_phase must be one of"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAA",
                "alg_key": "earnings_announcement_premium",
                "alg_param": {
                    "rows": _load_event_price_rows("earnings_after_close.csv"),
                    "event_rows": _earnings_event_rows(),
                    "event_value_field": "premium_score",
                    "bullish_phase": "during_event",
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match=r"event_rows\[0\] symbol is required"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAA",
                "alg_key": "index_rebalancing_effect_strategy",
                "alg_param": {
                    "rows": _load_event_price_rows("index_rebalance.csv"),
                    "event_rows": [
                        {
                            "event_timestamp": "2025-03-24 09:30:00",
                            "expected_flow": 0.80,
                        }
                    ],
                    "event_value_field": "expected_flow",
                },
                "buy": True,
                "sell": False,
            }
        )


def test_event_wave_1_performance_smoke_on_fixture_repetition(tmp_path: Path) -> None:
    earnings_rows = _load_event_price_rows("earnings_after_close.csv") * 150
    rebalance_rows = _load_event_price_rows("index_rebalance.csv") * 150
    algorithms = [
        (
            "post_earnings_announcement_drift",
            {
                "rows": earnings_rows,
                "event_rows": _earnings_event_rows(),
                "event_value_field": "surprise",
                "post_event_window_days": 2,
                "bullish_phase": "post_event",
            },
        ),
        (
            "pre_earnings_announcement_drift",
            {
                "rows": earnings_rows,
                "event_rows": _earnings_event_rows(),
                "event_value_field": "pre_drift_score",
                "pre_event_window_days": 1,
                "bullish_phase": "pre_event",
            },
        ),
        (
            "earnings_announcement_premium",
            {
                "rows": earnings_rows,
                "event_rows": _earnings_event_rows(),
                "event_value_field": "premium_score",
                "post_event_window_days": 1,
                "bullish_phase": "post_event",
            },
        ),
        (
            "index_rebalancing_effect_strategy",
            {
                "rows": rebalance_rows,
                "event_rows": _index_rebalance_event_rows(),
                "event_value_field": "expected_flow",
                "expected_direction_field": "expected_direction",
                "pre_event_window_days": 2,
                "bullish_phase": "pre_event",
            },
        ),
        (
            "etf_rebalancing_anticipation_front_run_strategy",
            {
                "rows": rebalance_rows,
                "event_rows": _index_rebalance_event_rows(),
                "event_value_field": "expected_flow",
                "expected_direction_field": "expected_direction",
                "pre_event_window_days": 3,
                "bullish_phase": "pre_event",
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "AAA",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        assert len(output.points) == len(
            cast(list[dict[str, object]], alg_param["rows"])
        )
        assert output.metadata["reporting_mode"] == "event_window"
        assert output.metadata["warmup_period"] == 1
