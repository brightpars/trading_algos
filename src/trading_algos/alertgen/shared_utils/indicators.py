from __future__ import annotations

import math
from collections import deque
from statistics import fmean
from typing import Sequence


def _validate_window(window: int) -> None:
    if window <= 0:
        raise ValueError("window must be positive")


def _as_float_list(values: Sequence[float | int | None]) -> list[float | None]:
    return [None if value is None else float(value) for value in values]


def simple_moving_average(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    result: list[float | None] = []
    queue: deque[float] = deque()
    total = 0.0
    for value in _as_float_list(values):
        if value is None:
            queue.clear()
            total = 0.0
            result.append(None)
            continue
        queue.append(value)
        total += value
        if len(queue) > window:
            total -= queue.popleft()
        result.append(total / window if len(queue) == window else None)
    return result


def exponential_moving_average(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    alpha = 2.0 / (window + 1.0)
    result: list[float | None] = []
    ema_value: float | None = None
    seed: list[float] = []
    for value in _as_float_list(values):
        if value is None:
            seed.clear()
            ema_value = None
            result.append(None)
            continue
        if ema_value is None:
            seed.append(value)
            if len(seed) < window:
                result.append(None)
                continue
            if len(seed) == window:
                ema_value = fmean(seed)
                result.append(ema_value)
                continue
        assert ema_value is not None
        ema_value = (value * alpha) + (ema_value * (1.0 - alpha))
        result.append(ema_value)
    return result


def detect_crossovers(
    fast_values: Sequence[float | None], slow_values: Sequence[float | None]
) -> list[str | None]:
    if len(fast_values) != len(slow_values):
        raise ValueError("fast_values and slow_values must have equal length")
    result: list[str | None] = []
    previous_spread: float | None = None
    for fast_value, slow_value in zip(fast_values, slow_values):
        if fast_value is None or slow_value is None:
            result.append(None)
            previous_spread = None
            continue
        spread = fast_value - slow_value
        if previous_spread is None:
            result.append(None)
        elif previous_spread <= 0.0 and spread > 0.0:
            result.append("bullish_cross")
        elif previous_spread >= 0.0 and spread < 0.0:
            result.append("bearish_cross")
        else:
            result.append(None)
        previous_spread = spread
    return result


def rolling_high(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    result: list[float | None] = []
    for index in range(len(values)):
        chunk = _as_float_list(values[max(0, index - window + 1) : index + 1])
        if len(chunk) < window or any(value is None for value in chunk):
            result.append(None)
            continue
        result.append(max(value for value in chunk if value is not None))
    return result


def rolling_low(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    result: list[float | None] = []
    for index in range(len(values)):
        chunk = _as_float_list(values[max(0, index - window + 1) : index + 1])
        if len(chunk) < window or any(value is None for value in chunk):
            result.append(None)
            continue
        result.append(min(value for value in chunk if value is not None))
    return result


def donchian_channel(
    highs: Sequence[float | int | None],
    lows: Sequence[float | int | None],
    window: int,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    upper = rolling_high(highs, window)
    lower = rolling_low(lows, window)
    middle = [
        None
        if upper_value is None or lower_value is None
        else (upper_value + lower_value) / 2.0
        for upper_value, lower_value in zip(upper, lower)
    ]
    return upper, lower, middle


def true_range(
    highs: Sequence[float | int | None],
    lows: Sequence[float | int | None],
    closes: Sequence[float | int | None],
) -> list[float | None]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must have equal length")
    result: list[float | None] = []
    previous_close: float | None = None
    for high, low, close in zip(
        _as_float_list(highs), _as_float_list(lows), _as_float_list(closes)
    ):
        if high is None or low is None or close is None:
            result.append(None)
            previous_close = None
            continue
        if previous_close is None:
            result.append(high - low)
        else:
            result.append(
                max(high - low, abs(high - previous_close), abs(low - previous_close))
            )
        previous_close = close
    return result


def average_true_range(
    highs: Sequence[float | int | None],
    lows: Sequence[float | int | None],
    closes: Sequence[float | int | None],
    window: int,
) -> list[float | None]:
    return simple_moving_average(true_range(highs, lows, closes), window)


def realized_volatility(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    returns: list[float | None] = [None]
    cast_values = _as_float_list(values)
    for previous, current in zip(cast_values, cast_values[1:]):
        if previous is None or previous == 0.0 or current is None:
            returns.append(None)
            continue
        returns.append(math.log(current / previous))
    return rolling_std(returns, window)


def rolling_mean(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    return simple_moving_average(values, window)


def rolling_std(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    result: list[float | None] = []
    cast_values = _as_float_list(values)
    for index in range(len(cast_values)):
        chunk = cast_values[max(0, index - window + 1) : index + 1]
        if len(chunk) < window or any(value is None for value in chunk):
            result.append(None)
            continue
        valid_chunk = [value for value in chunk if value is not None]
        mean_value = fmean(valid_chunk)
        variance = sum((value - mean_value) ** 2 for value in valid_chunk) / window
        result.append(math.sqrt(variance))
    return result


def rolling_zscore(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    means = rolling_mean(values, window)
    stds = rolling_std(values, window)
    result: list[float | None] = []
    for value, mean_value, std_value in zip(_as_float_list(values), means, stds):
        if value is None or mean_value is None or std_value in (None, 0.0):
            result.append(None)
            continue
        assert std_value is not None
        result.append((value - mean_value) / std_value)
    return result


def rate_of_change(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    cast_values = _as_float_list(values)
    result: list[float | None] = []
    for index, value in enumerate(cast_values):
        if index < window or value is None:
            result.append(None)
            continue
        base_value = cast_values[index - window]
        if base_value is None or base_value == 0.0:
            result.append(None)
            continue
        result.append(((value / base_value) - 1.0) * 100.0)
    return result


def momentum(values: Sequence[float | int | None], window: int) -> list[float | None]:
    _validate_window(window)
    cast_values = _as_float_list(values)
    result: list[float | None] = []
    for index, value in enumerate(cast_values):
        previous_value = cast_values[index - window] if index >= window else None
        if index < window or value is None or previous_value is None:
            result.append(None)
            continue
        result.append(value - previous_value)
    return result


def relative_strength_index(
    values: Sequence[float | int | None], window: int
) -> list[float | None]:
    _validate_window(window)
    cast_values = _as_float_list(values)
    gains: list[float | None] = [None]
    losses: list[float | None] = [None]
    for previous, current in zip(cast_values, cast_values[1:]):
        if previous is None or current is None:
            gains.append(None)
            losses.append(None)
            continue
        delta = current - previous
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = simple_moving_average(gains, window)
    avg_loss = simple_moving_average(losses, window)
    result: list[float | None] = []
    for gain_value, loss_value in zip(avg_gain, avg_loss):
        if gain_value is None or loss_value is None:
            result.append(None)
        elif loss_value == 0.0:
            result.append(100.0)
        else:
            rs = gain_value / loss_value
            result.append(100.0 - (100.0 / (1.0 + rs)))
    return result


def stochastic_oscillator(
    highs: Sequence[float | int | None],
    lows: Sequence[float | int | None],
    closes: Sequence[float | int | None],
    k_window: int,
    d_window: int,
) -> tuple[list[float | None], list[float | None]]:
    _validate_window(k_window)
    _validate_window(d_window)
    rolling_highs = rolling_high(highs, k_window)
    rolling_lows = rolling_low(lows, k_window)
    percent_k: list[float | None] = []
    for close, high_value, low_value in zip(
        _as_float_list(closes), rolling_highs, rolling_lows
    ):
        if close is None or high_value is None or low_value is None:
            percent_k.append(None)
        elif high_value == low_value:
            percent_k.append(0.0)
        else:
            percent_k.append(((close - low_value) / (high_value - low_value)) * 100.0)
    percent_d = simple_moving_average(percent_k, d_window)
    return percent_k, percent_d


def commodity_channel_index(
    highs: Sequence[float | int | None],
    lows: Sequence[float | int | None],
    closes: Sequence[float | int | None],
    window: int,
) -> list[float | None]:
    _validate_window(window)
    typical_price = [
        None
        if high is None or low is None or close is None
        else (high + low + close) / 3.0
        for high, low, close in zip(
            _as_float_list(highs), _as_float_list(lows), _as_float_list(closes)
        )
    ]
    sma = simple_moving_average(typical_price, window)
    result: list[float | None] = []
    for index, value in enumerate(typical_price):
        if index + 1 < window or value is None or sma[index] is None:
            result.append(None)
            continue
        chunk = typical_price[index - window + 1 : index + 1]
        if not all(item is not None for item in chunk):
            result.append(None)
            continue
        mean_value = sma[index]
        assert mean_value is not None
        mean_deviation = (
            sum(abs(item - mean_value) for item in chunk if item is not None) / window
        )
        if mean_deviation == 0.0:
            result.append(0.0)
            continue
        result.append((value - mean_value) / (0.015 * mean_deviation))
    return result


def macd(
    values: Sequence[float | int | None],
    fast_window: int = 12,
    slow_window: int = 26,
    signal_window: int = 9,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    fast_ema = exponential_moving_average(values, fast_window)
    slow_ema = exponential_moving_average(values, slow_window)
    macd_line = [
        None if fast_value is None or slow_value is None else fast_value - slow_value
        for fast_value, slow_value in zip(fast_ema, slow_ema)
    ]
    signal_line = exponential_moving_average(macd_line, signal_window)
    histogram = [
        None
        if line_value is None or signal_value is None
        else line_value - signal_value
        for line_value, signal_value in zip(macd_line, signal_line)
    ]
    return macd_line, signal_line, histogram


def rolling_linear_regression(
    values: Sequence[float | int | None], window: int
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    _validate_window(window)
    cast_values = _as_float_list(values)
    slopes: list[float | None] = []
    intercepts: list[float | None] = []
    r_squared_values: list[float | None] = []
    x_values = list(range(window))
    x_mean = fmean(x_values)
    x_variance = sum((value - x_mean) ** 2 for value in x_values)
    for index in range(len(cast_values)):
        chunk = cast_values[max(0, index - window + 1) : index + 1]
        if len(chunk) < window or any(value is None for value in chunk):
            slopes.append(None)
            intercepts.append(None)
            r_squared_values.append(None)
            continue
        valid_chunk = [value for value in chunk if value is not None]
        y_mean = fmean(valid_chunk)
        covariance = sum(
            (x_value - x_mean) * (y_value - y_mean)
            for x_value, y_value in zip(x_values, valid_chunk)
        )
        slope = covariance / x_variance if x_variance else 0.0
        intercept = y_mean - (slope * x_mean)
        predicted = [(slope * x_value) + intercept for x_value in x_values]
        ss_tot = sum((y_value - y_mean) ** 2 for y_value in valid_chunk)
        ss_res = sum(
            (y_value - predicted_value) ** 2
            for y_value, predicted_value in zip(valid_chunk, predicted)
        )
        r_squared = None if ss_tot == 0.0 else 1.0 - (ss_res / ss_tot)
        slopes.append(slope)
        intercepts.append(intercept)
        r_squared_values.append(r_squared)
    return slopes, intercepts, r_squared_values
