import pytest

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.indicators import (
    average_true_range,
    detect_crossovers,
    exponential_moving_average,
    macd,
    rate_of_change,
    relative_strength_index,
    rolling_linear_regression,
    rolling_zscore,
    simple_moving_average,
    stochastic_oscillator,
)


def test_simple_and_exponential_moving_averages_return_expected_shapes() -> None:
    values = [1, 2, 3, 4, 5]

    sma = simple_moving_average(values, 3)
    ema = exponential_moving_average(values, 3)

    assert sma == [None, None, 2.0, 3.0, 4.0]
    assert ema[:2] == [None, None]
    assert ema[2] == pytest.approx(2.0)
    assert ema[-1] == pytest.approx(4.0)


def test_detect_crossovers_marks_bullish_and_bearish_transitions() -> None:
    fast = [None, 1.0, 2.0, 1.0, 0.0]
    slow = [None, 2.0, 1.0, 1.5, 1.0]

    result = detect_crossovers(fast, slow)

    assert result == [None, None, "bullish_cross", "bearish_cross", None]


def test_volatility_momentum_and_oscillator_helpers_compute_expected_points() -> None:
    highs = [10, 12, 13, 14, 15]
    lows = [8, 10, 11, 12, 13]
    closes = [9, 11, 12, 13, 14]

    atr = average_true_range(highs, lows, closes, 3)
    roc = rate_of_change(closes, 2)
    rsi = relative_strength_index(closes, 2)
    percent_k, percent_d = stochastic_oscillator(highs, lows, closes, 3, 2)

    assert atr == [
        None,
        None,
        pytest.approx(2.3333333333),
        pytest.approx(2.3333333333),
        2.0,
    ]
    assert roc == [
        None,
        None,
        pytest.approx(33.3333333333),
        pytest.approx(18.1818181818),
        pytest.approx(16.6666666667),
    ]
    assert rsi[:2] == [None, None]
    assert rsi[-1] == 100.0
    assert percent_k[:2] == [None, None]
    assert percent_k[-1] == pytest.approx(75.0)
    assert percent_d[-1] == pytest.approx(75.0)


def test_zscore_macd_and_regression_helpers_produce_expected_outputs() -> None:
    values = [1, 2, 3, 4, 5, 6]

    zscores = rolling_zscore(values, 3)
    macd_line, signal_line, histogram = macd(
        values, fast_window=2, slow_window=3, signal_window=2
    )
    slopes, intercepts, r_squared_values = rolling_linear_regression(values, 3)

    assert zscores[:2] == [None, None]
    assert zscores[2] == pytest.approx(1.2247448714)
    assert macd_line[-1] is not None
    assert signal_line[-1] is not None
    assert histogram[-1] == pytest.approx(macd_line[-1] - signal_line[-1])
    assert slopes[:2] == [None, None]
    assert slopes[-1] == pytest.approx(1.0)
    assert intercepts[-1] == pytest.approx(4.0)
    assert r_squared_values[-1] == pytest.approx(1.0)


def test_normalized_child_output_contract_validates_and_serializes() -> None:
    child_output = NormalizedChildOutput(
        child_key="sample_child",
        output_kind="composite_child",
        signal_label="buy",
        score=1.0,
        confidence=0.8,
        regime_label="UP",
        direction=1,
        diagnostics={"window": 5},
        reason_codes=("alg_name",),
    )
    output = AlertAlgorithmOutput(
        algorithm_key="sample_alg",
        points=(
            AlertSeriesPoint(
                timestamp="2025-01-01 10:00:00",
                signal_label="buy",
                score=1.0,
                confidence=0.8,
            ),
        ),
        derived_series={"close": [10.0]},
        metadata={"output_contract_version": "1.0"},
        child_outputs=(child_output,),
    )

    payload = output.to_dict()

    assert payload["child_outputs"][0]["child_key"] == "sample_child"
    assert payload["points"][0]["confidence"] == 0.8


def test_output_contract_rejects_invalid_shapes_and_ranges() -> None:
    with pytest.raises(ValueError, match="unsupported signal_label"):
        AlertSeriesPoint(timestamp="2025", signal_label="hold")

    with pytest.raises(ValueError, match="confidence must be within"):
        NormalizedChildOutput(
            child_key="sample_child",
            output_kind="composite_child",
            signal_label="buy",
            confidence=1.5,
        )

    with pytest.raises(ValueError, match="derived series length mismatch"):
        AlertAlgorithmOutput(
            algorithm_key="sample_alg",
            points=(AlertSeriesPoint(timestamp="2025", signal_label="buy"),),
            derived_series={"close": [1.0, 2.0]},
        )
