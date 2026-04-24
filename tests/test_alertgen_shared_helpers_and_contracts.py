import pytest

from trading_algos.alertgen.algorithms.composite.rule_based_combination.helpers import (
    align_child_outputs,
)
from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.indicators import (
    average_true_range,
    compression_ratio,
    detect_crossovers,
    directional_movement_index,
    exponential_moving_average,
    ichimoku,
    macd,
    parabolic_sar,
    rate_of_change,
    relative_strength_index,
    rolling_linear_regression,
    rolling_price_range,
    rolling_zscore,
    simple_moving_average,
    stochastic_oscillator,
    supertrend,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    cumulative_session_vwap,
    rolling_ou_reversion_ratio,
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


def test_volatility_compression_helpers_compute_expected_shapes() -> None:
    highs = [10.0, 10.2, 10.1, 10.15, 10.2, 10.9]
    lows = [9.8, 9.9, 9.95, 10.0, 10.0, 10.2]
    closes = [10.0, 10.05, 10.0, 10.1, 10.15, 10.8]

    price_ranges = rolling_price_range(highs, lows, 3)
    atr_values, compression_ranges, ratio_values = compression_ratio(
        highs, lows, closes, atr_window=3, compression_window=3
    )

    assert price_ranges[:2] == [None, None]
    assert price_ranges[-1] == pytest.approx(0.9)
    assert atr_values[-1] is not None
    assert compression_ranges[-1] == pytest.approx(price_ranges[-1])
    assert ratio_values[-1] is not None


def test_trend_batch_two_indicator_helpers_produce_expected_shapes() -> None:
    highs = [10, 11, 12, 13, 14, 15]
    lows = [9, 10, 11, 12, 13, 14]
    closes = [9.5, 10.5, 11.5, 12.5, 13.5, 14.5]

    plus_di, minus_di, adx_values = directional_movement_index(highs, lows, closes, 3)
    sar_values = parabolic_sar(highs, lows, step=0.02, max_step=0.2)
    upper_band, lower_band, direction = supertrend(highs, lows, closes, 3, 2.0)

    assert len(plus_di) == len(highs)
    assert len(minus_di) == len(highs)
    assert len(adx_values) == len(highs)
    assert adx_values[-1] is not None
    assert sar_values[-1] is not None
    assert len(upper_band) == len(highs)
    assert len(lower_band) == len(highs)
    assert direction[-1] in (-1, 1)


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


def test_mean_reversion_wave_3_shared_helpers_compute_session_vwap_and_ou_state() -> (
    None
):
    timestamps = [
        "2025-01-01 09:30:00",
        "2025-01-01 09:35:00",
        "2025-01-02 09:30:00",
    ]
    highs = [10.0, 11.0, 12.0]
    lows = [9.0, 10.0, 11.0]
    closes = [9.5, 10.5, 11.5]
    volumes = [100.0, 200.0, 300.0]

    vwap_values = cumulative_session_vwap(timestamps, highs, lows, closes, volumes)
    mean_reversion_speed, equilibrium, residual, residual_zscore = (
        rolling_ou_reversion_ratio([100.0, 99.0, 98.0, 99.0, 100.0], 4)
    )

    assert vwap_values[0] == pytest.approx(9.5)
    assert vwap_values[1] == pytest.approx((9.5 * 100.0 + 10.5 * 200.0) / 300.0)
    assert vwap_values[2] == pytest.approx(11.5)
    assert mean_reversion_speed[-1] is not None
    assert equilibrium[-1] is not None
    assert residual[-1] is not None
    assert residual_zscore[-1] is not None


def test_ichimoku_helper_produces_expected_shapes() -> None:
    highs = [10, 11, 12, 13, 14, 15]
    lows = [9, 10, 11, 12, 13, 14]
    closes = [9.5, 10.5, 11.5, 12.5, 13.5, 14.5]

    conversion, base, span_a, span_b, lagging = ichimoku(
        highs,
        lows,
        closes,
        conversion_window=2,
        base_window=3,
        span_b_window=4,
        displacement=2,
    )

    assert len(conversion) == len(highs)
    assert len(base) == len(highs)
    assert len(span_a) == len(highs)
    assert len(span_b) == len(highs)
    assert len(lagging) == len(highs)
    assert conversion[-1] == pytest.approx(14.0)
    assert base[-1] == pytest.approx(13.5)
    assert span_a[-1] == pytest.approx(13.75)
    assert span_b[-1] == pytest.approx(13.0)
    assert lagging[-1] == pytest.approx(12.5)


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


def test_align_child_outputs_normalizes_child_stream_rows() -> None:
    rows = align_child_outputs(
        [
            {
                "timestamp": "2025-01-01T00:00:00Z",
                "child_outputs": [
                    {
                        "child_key": "a",
                        "signal_label": "buy",
                        "score": 1.2,
                        "confidence": 1.5,
                    },
                    {"child_key": "b", "signal_label": "neutral", "score": 0.0},
                ],
            }
        ]
    )

    assert rows[0].timestamp == "2025-01-01T00:00:00Z"
    assert rows[0].child_outputs[0].score == 1.0
    assert rows[0].child_outputs[0].confidence == 1.0
    assert rows[0].child_outputs[1].direction == 0
