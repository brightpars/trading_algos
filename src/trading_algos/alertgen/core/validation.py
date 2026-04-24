import json

from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)


def _validate_required_keys(payload, required_keys, label):
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing_keys)}")


def _normalize_bool_like(value, label):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ["true", "1", "yes", "y", "t"]:
            return True
        if normalized in ["false", "0", "no", "n", "f"]:
            return False
    if isinstance(value, int) and value in [0, 1]:
        return bool(value)
    raise ValueError(f"{label} must be a boolean")


def _require_non_empty_string(value, label, *, reject_random_name=False):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{label} is required")
    if reject_random_name and normalized.lower() == "random-name":
        raise ValueError(f"{label} is invalid")
    return normalized


def _require_int_like(value, label):
    try:
        return int(value)
    except Exception as exc:
        raise ValueError(f"{label} must be an integer: {exc}")


def _require_positive_int_like(value, label):
    parsed = _require_int_like(value, label)
    if parsed <= 0:
        raise ValueError(f"{label} must be > 0")
    return parsed


def _require_json_object_dict(raw, label):
    if isinstance(raw, dict):
        return dict(raw)
    if not isinstance(raw, str):
        raise ValueError(f"{label} must be a dict/JSON object.")
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"{label} must be a dict/JSON object: {exc}")
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a dict/JSON object.")
    return parsed


def _normalize_alertgen_alg_param(*, alg_key, raw_alg_param, label):
    from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms

    register_builtin_alert_algorithms()
    spec = get_alert_algorithm_spec_by_key(alg_key)
    return spec.param_normalizer(raw_alg_param, label)


def _require_param_dict(raw_alg_param, label):
    if not isinstance(raw_alg_param, dict):
        raise ValueError(f"{label} must be a dict/JSON object")
    return dict(raw_alg_param)


def _require_single_positive_int_param(raw_alg_param, label, *, field_name):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(normalized, [field_name], label)
    return {
        field_name: _require_positive_int_like(
            normalized[field_name], f"{label} {field_name}"
        )
    }


def require_period_param(raw_alg_param, label):
    return _require_single_positive_int_param(raw_alg_param, label, field_name="period")


def require_window_param(raw_alg_param, label):
    return _require_single_positive_int_param(raw_alg_param, label, field_name="window")


def require_buy_sell_window_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(normalized, ["buy_window", "sell_window"], label)
    return {
        "buy_window": _require_positive_int_like(
            normalized["buy_window"], f"{label} buy_window"
        ),
        "sell_window": _require_positive_int_like(
            normalized["sell_window"], f"{label} sell_window"
        ),
    }


def _require_non_negative_float_like(value, label):
    try:
        parsed = float(value)
    except Exception as exc:
        raise ValueError(f"{label} must be a number: {exc}")
    if parsed < 0.0:
        raise ValueError(f"{label} must be >= 0")
    return parsed


def _require_positive_float_list(value, label, *, minimum_length=1):
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    normalized = []
    for index, item in enumerate(value):
        parsed = _require_non_negative_float_like(item, f"{label}[{index}]")
        if parsed == 0.0:
            raise ValueError(f"{label}[{index}] must be > 0")
        normalized.append(parsed)
    if len(normalized) < minimum_length:
        raise ValueError(f"{label} must contain at least {minimum_length} items")
    return normalized


def _require_choice(value, label, *, allowed):
    normalized = _require_non_empty_string(value, label).lower()
    if normalized not in allowed:
        allowed_csv = ", ".join(sorted(allowed))
        raise ValueError(f"{label} must be one of: {allowed_csv}")
    return normalized


def _require_positive_int_list(value, label, *, minimum_length=1):
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    normalized = [
        _require_positive_int_like(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(normalized) < minimum_length:
        raise ValueError(f"{label} must contain at least {minimum_length} items")
    return normalized


def _require_non_empty_string_list(value, label, *, minimum_length=1):
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    normalized = [
        _require_non_empty_string(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(normalized) < minimum_length:
        raise ValueError(f"{label} must contain at least {minimum_length} items")
    return normalized


def require_short_long_window_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["short_window", "long_window", "minimum_spread", "confirmation_bars"],
        label,
    )
    short_window = _require_positive_int_like(
        normalized["short_window"], f"{label} short_window"
    )
    long_window = _require_positive_int_like(
        normalized["long_window"], f"{label} long_window"
    )
    if short_window >= long_window:
        raise ValueError(f"{label} requires short_window < long_window")
    return {
        "short_window": short_window,
        "long_window": long_window,
        "minimum_spread": _require_non_negative_float_like(
            normalized["minimum_spread"], f"{label} minimum_spread"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_fast_medium_slow_window_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "fast_window",
            "medium_window",
            "slow_window",
            "minimum_spread",
            "confirmation_bars",
        ],
        label,
    )
    fast_window = _require_positive_int_like(
        normalized["fast_window"], f"{label} fast_window"
    )
    medium_window = _require_positive_int_like(
        normalized["medium_window"], f"{label} medium_window"
    )
    slow_window = _require_positive_int_like(
        normalized["slow_window"], f"{label} slow_window"
    )
    if not (fast_window < medium_window < slow_window):
        raise ValueError(f"{label} requires fast_window < medium_window < slow_window")
    return {
        "fast_window": fast_window,
        "medium_window": medium_window,
        "slow_window": slow_window,
        "minimum_spread": _require_non_negative_float_like(
            normalized["minimum_spread"], f"{label} minimum_spread"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_price_vs_ma_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "average_type", "minimum_spread", "confirmation_bars"],
        label,
    )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "average_type": _require_choice(
            normalized["average_type"],
            f"{label} average_type",
            allowed={"sma", "ema"},
        ),
        "minimum_spread": _require_non_negative_float_like(
            normalized["minimum_spread"], f"{label} minimum_spread"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_ribbon_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["windows", "minimum_spread", "confirmation_bars"],
        label,
    )
    windows = _require_positive_int_list(
        normalized["windows"], f"{label} windows", minimum_length=3
    )
    if len(set(windows)) != len(windows):
        raise ValueError(f"{label} windows must not contain duplicates")
    sorted_windows = sorted(windows)
    if windows != sorted_windows:
        raise ValueError(f"{label} windows must be sorted ascending")
    return {
        "windows": windows,
        "minimum_spread": _require_non_negative_float_like(
            normalized["minimum_spread"], f"{label} minimum_spread"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_breakout_donchian_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "minimum_breakout", "confirmation_bars"],
        label,
    )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "minimum_breakout": _require_non_negative_float_like(
            normalized["minimum_breakout"], f"{label} minimum_breakout"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_channel_confirmation_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "breakout_threshold", "confirmation_bars"],
        label,
    )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "breakout_threshold": _require_non_negative_float_like(
            normalized["breakout_threshold"], f"{label} breakout_threshold"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_adx_trend_filter_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "adx_threshold", "confirmation_bars"],
        label,
    )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "adx_threshold": _require_non_negative_float_like(
            normalized["adx_threshold"], f"{label} adx_threshold"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_parabolic_sar_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["step", "max_step", "confirmation_bars"],
        label,
    )
    step = _require_non_negative_float_like(normalized["step"], f"{label} step")
    max_step = _require_non_negative_float_like(
        normalized["max_step"], f"{label} max_step"
    )
    if step == 0.0:
        raise ValueError(f"{label} step must be > 0")
    if max_step < step:
        raise ValueError(f"{label} requires max_step >= step")
    return {
        "step": step,
        "max_step": max_step,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_supertrend_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "multiplier", "confirmation_bars"],
        label,
    )
    multiplier = _require_non_negative_float_like(
        normalized["multiplier"], f"{label} multiplier"
    )
    if multiplier == 0.0:
        raise ValueError(f"{label} multiplier must be > 0")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "multiplier": multiplier,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_ichimoku_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "conversion_window",
            "base_window",
            "span_b_window",
            "displacement",
            "minimum_cloud_gap",
            "confirmation_bars",
        ],
        label,
    )
    conversion_window = _require_positive_int_like(
        normalized["conversion_window"], f"{label} conversion_window"
    )
    base_window = _require_positive_int_like(
        normalized["base_window"], f"{label} base_window"
    )
    span_b_window = _require_positive_int_like(
        normalized["span_b_window"], f"{label} span_b_window"
    )
    displacement = _require_positive_int_like(
        normalized["displacement"], f"{label} displacement"
    )
    if not (conversion_window < base_window < span_b_window):
        raise ValueError(
            f"{label} requires conversion_window < base_window < span_b_window"
        )
    return {
        "conversion_window": conversion_window,
        "base_window": base_window,
        "span_b_window": span_b_window,
        "displacement": displacement,
        "minimum_cloud_gap": _require_non_negative_float_like(
            normalized["minimum_cloud_gap"], f"{label} minimum_cloud_gap"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_macd_trend_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "fast_window",
            "slow_window",
            "signal_window",
            "histogram_threshold",
            "confirmation_bars",
        ],
        label,
    )
    fast_window = _require_positive_int_like(
        normalized["fast_window"], f"{label} fast_window"
    )
    slow_window = _require_positive_int_like(
        normalized["slow_window"], f"{label} slow_window"
    )
    signal_window = _require_positive_int_like(
        normalized["signal_window"], f"{label} signal_window"
    )
    if fast_window >= slow_window:
        raise ValueError(f"{label} requires fast_window < slow_window")
    return {
        "fast_window": fast_window,
        "slow_window": slow_window,
        "signal_window": signal_window,
        "histogram_threshold": _require_non_negative_float_like(
            normalized["histogram_threshold"], f"{label} histogram_threshold"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_linear_regression_trend_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "slope_threshold", "min_r_squared", "confirmation_bars"],
        label,
    )
    min_r_squared = _require_non_negative_float_like(
        normalized["min_r_squared"], f"{label} min_r_squared"
    )
    if min_r_squared > 1.0:
        raise ValueError(f"{label} min_r_squared must be <= 1")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "slope_threshold": _require_non_negative_float_like(
            normalized["slope_threshold"], f"{label} slope_threshold"
        ),
        "min_r_squared": min_r_squared,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_time_series_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "return_threshold", "confirmation_bars"],
        label,
    )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "return_threshold": _require_non_negative_float_like(
            normalized["return_threshold"], f"{label} return_threshold"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_roc_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "bullish_threshold", "bearish_threshold", "confirmation_bars"],
        label,
    )
    bullish_threshold = _require_float_like(
        normalized["bullish_threshold"], f"{label} bullish_threshold"
    )
    bearish_threshold = _require_float_like(
        normalized["bearish_threshold"], f"{label} bearish_threshold"
    )
    if bearish_threshold > bullish_threshold:
        raise ValueError(f"{label} requires bearish_threshold <= bullish_threshold")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "bullish_threshold": bullish_threshold,
        "bearish_threshold": bearish_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_accelerating_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "fast_window",
            "slow_window",
            "acceleration_threshold",
            "bearish_threshold",
            "confirmation_bars",
        ],
        label,
    )
    fast_window = _require_positive_int_like(
        normalized["fast_window"], f"{label} fast_window"
    )
    slow_window = _require_positive_int_like(
        normalized["slow_window"], f"{label} slow_window"
    )
    if fast_window >= slow_window:
        raise ValueError(f"{label} requires fast_window < slow_window")
    acceleration_threshold = _require_float_like(
        normalized["acceleration_threshold"], f"{label} acceleration_threshold"
    )
    bearish_threshold = _require_float_like(
        normalized["bearish_threshold"], f"{label} bearish_threshold"
    )
    if bearish_threshold > acceleration_threshold:
        raise ValueError(
            f"{label} requires bearish_threshold <= acceleration_threshold"
        )
    return {
        "fast_window": fast_window,
        "slow_window": slow_window,
        "acceleration_threshold": acceleration_threshold,
        "bearish_threshold": bearish_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_rsi_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "bullish_threshold", "bearish_threshold", "confirmation_bars"],
        label,
    )
    bullish_threshold = _require_float_like(
        normalized["bullish_threshold"], f"{label} bullish_threshold"
    )
    bearish_threshold = _require_float_like(
        normalized["bearish_threshold"], f"{label} bearish_threshold"
    )
    if not 0.0 <= bearish_threshold <= 100.0:
        raise ValueError(f"{label} bearish_threshold must be within [0, 100]")
    if not 0.0 <= bullish_threshold <= 100.0:
        raise ValueError(f"{label} bullish_threshold must be within [0, 100]")
    if bearish_threshold > bullish_threshold:
        raise ValueError(f"{label} requires bearish_threshold <= bullish_threshold")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "bullish_threshold": bullish_threshold,
        "bearish_threshold": bearish_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_stochastic_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "k_window",
            "d_window",
            "bullish_threshold",
            "bearish_threshold",
            "confirmation_bars",
        ],
        label,
    )
    bullish_threshold = _require_float_like(
        normalized["bullish_threshold"], f"{label} bullish_threshold"
    )
    bearish_threshold = _require_float_like(
        normalized["bearish_threshold"], f"{label} bearish_threshold"
    )
    if not 0.0 <= bearish_threshold <= 100.0:
        raise ValueError(f"{label} bearish_threshold must be within [0, 100]")
    if not 0.0 <= bullish_threshold <= 100.0:
        raise ValueError(f"{label} bullish_threshold must be within [0, 100]")
    if bearish_threshold > bullish_threshold:
        raise ValueError(f"{label} requires bearish_threshold <= bullish_threshold")
    return {
        "k_window": _require_positive_int_like(
            normalized["k_window"], f"{label} k_window"
        ),
        "d_window": _require_positive_int_like(
            normalized["d_window"], f"{label} d_window"
        ),
        "bullish_threshold": bullish_threshold,
        "bearish_threshold": bearish_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_cci_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "bullish_threshold", "bearish_threshold", "confirmation_bars"],
        label,
    )
    bullish_threshold = _require_float_like(
        normalized["bullish_threshold"], f"{label} bullish_threshold"
    )
    bearish_threshold = _require_float_like(
        normalized["bearish_threshold"], f"{label} bearish_threshold"
    )
    if bearish_threshold > bullish_threshold:
        raise ValueError(f"{label} requires bearish_threshold <= bullish_threshold")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "bullish_threshold": bullish_threshold,
        "bearish_threshold": bearish_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_kst_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "roc_windows",
            "smoothing_windows",
            "signal_window",
            "entry_mode",
            "confirmation_bars",
        ],
        label,
    )
    roc_windows = _require_positive_int_list(
        normalized["roc_windows"], f"{label} roc_windows", minimum_length=2
    )
    smoothing_windows = _require_positive_int_list(
        normalized["smoothing_windows"],
        f"{label} smoothing_windows",
        minimum_length=2,
    )
    if len(roc_windows) != len(smoothing_windows):
        raise ValueError(
            f"{label} requires roc_windows and smoothing_windows to have equal length"
        )
    return {
        "roc_windows": roc_windows,
        "smoothing_windows": smoothing_windows,
        "signal_window": _require_positive_int_like(
            normalized["signal_window"], f"{label} signal_window"
        ),
        "entry_mode": _require_choice(
            normalized["entry_mode"],
            f"{label} entry_mode",
            allowed={"signal_cross", "zero_cross"},
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_volume_confirmed_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "momentum_window",
            "volume_window",
            "relative_volume_threshold",
            "signal_threshold",
            "confirmation_bars",
        ],
        label,
    )
    relative_volume_threshold = _require_non_negative_float_like(
        normalized["relative_volume_threshold"],
        f"{label} relative_volume_threshold",
    )
    if relative_volume_threshold == 0.0:
        raise ValueError(f"{label} relative_volume_threshold must be > 0")
    signal_threshold = _require_non_negative_float_like(
        normalized["signal_threshold"], f"{label} signal_threshold"
    )
    return {
        "momentum_window": _require_positive_int_like(
            normalized["momentum_window"], f"{label} momentum_window"
        ),
        "volume_window": _require_positive_int_like(
            normalized["volume_window"], f"{label} volume_window"
        ),
        "relative_volume_threshold": relative_volume_threshold,
        "signal_threshold": signal_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_zscore_mean_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "entry_zscore", "exit_zscore", "confirmation_bars"],
        label,
    )
    entry_zscore = _require_non_negative_float_like(
        normalized["entry_zscore"], f"{label} entry_zscore"
    )
    exit_zscore = _require_non_negative_float_like(
        normalized["exit_zscore"], f"{label} exit_zscore"
    )
    if exit_zscore > entry_zscore:
        raise ValueError(f"{label} requires exit_zscore <= entry_zscore")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "entry_zscore": entry_zscore,
        "exit_zscore": exit_zscore,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_bollinger_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "std_multiplier", "exit_band_fraction", "confirmation_bars"],
        label,
    )
    exit_band_fraction = _require_non_negative_float_like(
        normalized["exit_band_fraction"], f"{label} exit_band_fraction"
    )
    if exit_band_fraction > 1.0:
        raise ValueError(f"{label} exit_band_fraction must be <= 1")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "std_multiplier": _require_non_negative_float_like(
            normalized["std_multiplier"], f"{label} std_multiplier"
        ),
        "exit_band_fraction": exit_band_fraction,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_rsi_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "window",
            "oversold_threshold",
            "overbought_threshold",
            "exit_threshold",
            "confirmation_bars",
        ],
        label,
    )
    oversold_threshold = _require_float_like(
        normalized["oversold_threshold"], f"{label} oversold_threshold"
    )
    overbought_threshold = _require_float_like(
        normalized["overbought_threshold"], f"{label} overbought_threshold"
    )
    exit_threshold = _require_float_like(
        normalized["exit_threshold"], f"{label} exit_threshold"
    )
    if not 0.0 <= oversold_threshold <= 100.0:
        raise ValueError(f"{label} oversold_threshold must be within [0, 100]")
    if not 0.0 <= overbought_threshold <= 100.0:
        raise ValueError(f"{label} overbought_threshold must be within [0, 100]")
    if not 0.0 <= exit_threshold <= 100.0:
        raise ValueError(f"{label} exit_threshold must be within [0, 100]")
    if oversold_threshold >= overbought_threshold:
        raise ValueError(f"{label} requires oversold_threshold < overbought_threshold")
    if not oversold_threshold <= exit_threshold <= overbought_threshold:
        raise ValueError(
            f"{label} requires oversold_threshold <= exit_threshold <= overbought_threshold"
        )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "oversold_threshold": oversold_threshold,
        "overbought_threshold": overbought_threshold,
        "exit_threshold": exit_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_stochastic_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "k_window",
            "d_window",
            "oversold_threshold",
            "overbought_threshold",
            "exit_threshold",
            "confirmation_bars",
        ],
        label,
    )
    oversold_threshold = _require_float_like(
        normalized["oversold_threshold"], f"{label} oversold_threshold"
    )
    overbought_threshold = _require_float_like(
        normalized["overbought_threshold"], f"{label} overbought_threshold"
    )
    exit_threshold = _require_float_like(
        normalized["exit_threshold"], f"{label} exit_threshold"
    )
    if not 0.0 <= oversold_threshold <= 100.0:
        raise ValueError(f"{label} oversold_threshold must be within [0, 100]")
    if not 0.0 <= overbought_threshold <= 100.0:
        raise ValueError(f"{label} overbought_threshold must be within [0, 100]")
    if not 0.0 <= exit_threshold <= 100.0:
        raise ValueError(f"{label} exit_threshold must be within [0, 100]")
    if oversold_threshold >= overbought_threshold:
        raise ValueError(f"{label} requires oversold_threshold < overbought_threshold")
    if not oversold_threshold <= exit_threshold <= overbought_threshold:
        raise ValueError(
            f"{label} requires oversold_threshold <= exit_threshold <= overbought_threshold"
        )
    return {
        "k_window": _require_positive_int_like(
            normalized["k_window"], f"{label} k_window"
        ),
        "d_window": _require_positive_int_like(
            normalized["d_window"], f"{label} d_window"
        ),
        "oversold_threshold": oversold_threshold,
        "overbought_threshold": overbought_threshold,
        "exit_threshold": exit_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_cci_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "window",
            "oversold_threshold",
            "overbought_threshold",
            "exit_threshold",
            "confirmation_bars",
        ],
        label,
    )
    oversold_threshold = _require_float_like(
        normalized["oversold_threshold"], f"{label} oversold_threshold"
    )
    overbought_threshold = _require_float_like(
        normalized["overbought_threshold"], f"{label} overbought_threshold"
    )
    exit_threshold = _require_float_like(
        normalized["exit_threshold"], f"{label} exit_threshold"
    )
    if oversold_threshold >= overbought_threshold:
        raise ValueError(f"{label} requires oversold_threshold < overbought_threshold")
    if not oversold_threshold <= exit_threshold <= overbought_threshold:
        raise ValueError(
            f"{label} requires oversold_threshold <= exit_threshold <= overbought_threshold"
        )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "oversold_threshold": oversold_threshold,
        "overbought_threshold": overbought_threshold,
        "exit_threshold": exit_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_williams_percent_r_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "window",
            "oversold_threshold",
            "overbought_threshold",
            "exit_threshold",
            "confirmation_bars",
        ],
        label,
    )
    oversold_threshold = _require_float_like(
        normalized["oversold_threshold"], f"{label} oversold_threshold"
    )
    overbought_threshold = _require_float_like(
        normalized["overbought_threshold"], f"{label} overbought_threshold"
    )
    exit_threshold = _require_float_like(
        normalized["exit_threshold"], f"{label} exit_threshold"
    )
    if not -100.0 <= oversold_threshold <= 0.0:
        raise ValueError(f"{label} oversold_threshold must be within [-100, 0]")
    if not -100.0 <= overbought_threshold <= 0.0:
        raise ValueError(f"{label} overbought_threshold must be within [-100, 0]")
    if not -100.0 <= exit_threshold <= 0.0:
        raise ValueError(f"{label} exit_threshold must be within [-100, 0]")
    if oversold_threshold >= overbought_threshold:
        raise ValueError(f"{label} requires oversold_threshold < overbought_threshold")
    if not oversold_threshold <= exit_threshold <= overbought_threshold:
        raise ValueError(
            f"{label} requires oversold_threshold <= exit_threshold <= overbought_threshold"
        )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "oversold_threshold": oversold_threshold,
        "overbought_threshold": overbought_threshold,
        "exit_threshold": exit_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_range_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["window", "entry_band_fraction", "exit_band_fraction", "confirmation_bars"],
        label,
    )
    entry_band_fraction = _require_non_negative_float_like(
        normalized["entry_band_fraction"], f"{label} entry_band_fraction"
    )
    exit_band_fraction = _require_non_negative_float_like(
        normalized["exit_band_fraction"], f"{label} exit_band_fraction"
    )
    if entry_band_fraction >= 0.5:
        raise ValueError(f"{label} entry_band_fraction must be < 0.5")
    if exit_band_fraction > 0.5:
        raise ValueError(f"{label} exit_band_fraction must be <= 0.5")
    if exit_band_fraction < entry_band_fraction:
        raise ValueError(f"{label} requires entry_band_fraction <= exit_band_fraction")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "entry_band_fraction": entry_band_fraction,
        "exit_band_fraction": exit_band_fraction,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_long_horizon_reversal_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "window",
            "entry_return_threshold",
            "exit_return_threshold",
            "confirmation_bars",
        ],
        label,
    )
    entry_return_threshold = _require_non_negative_float_like(
        normalized["entry_return_threshold"], f"{label} entry_return_threshold"
    )
    exit_return_threshold = _require_non_negative_float_like(
        normalized["exit_return_threshold"], f"{label} exit_return_threshold"
    )
    if entry_return_threshold == 0.0:
        raise ValueError(f"{label} entry_return_threshold must be > 0")
    if exit_return_threshold > entry_return_threshold:
        raise ValueError(
            f"{label} requires exit_return_threshold <= entry_return_threshold"
        )
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "entry_return_threshold": entry_return_threshold,
        "exit_return_threshold": exit_return_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_volatility_adjusted_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "window",
            "atr_window",
            "entry_atr_multiple",
            "exit_atr_multiple",
            "confirmation_bars",
        ],
        label,
    )
    entry_atr_multiple = _require_non_negative_float_like(
        normalized["entry_atr_multiple"], f"{label} entry_atr_multiple"
    )
    exit_atr_multiple = _require_non_negative_float_like(
        normalized["exit_atr_multiple"], f"{label} exit_atr_multiple"
    )
    if entry_atr_multiple == 0.0:
        raise ValueError(f"{label} entry_atr_multiple must be > 0")
    if exit_atr_multiple > entry_atr_multiple:
        raise ValueError(f"{label} requires exit_atr_multiple <= entry_atr_multiple")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "atr_window": _require_positive_int_like(
            normalized["atr_window"], f"{label} atr_window"
        ),
        "entry_atr_multiple": entry_atr_multiple,
        "exit_atr_multiple": exit_atr_multiple,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_intraday_vwap_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "entry_deviation_percent",
            "exit_deviation_percent",
            "min_session_bars",
            "confirmation_bars",
        ],
        label,
    )
    entry_deviation_percent = _require_non_negative_float_like(
        normalized["entry_deviation_percent"], f"{label} entry_deviation_percent"
    )
    exit_deviation_percent = _require_non_negative_float_like(
        normalized["exit_deviation_percent"], f"{label} exit_deviation_percent"
    )
    if entry_deviation_percent == 0.0:
        raise ValueError(f"{label} entry_deviation_percent must be > 0")
    if exit_deviation_percent > entry_deviation_percent:
        raise ValueError(
            f"{label} requires exit_deviation_percent <= entry_deviation_percent"
        )
    return {
        "entry_deviation_percent": entry_deviation_percent,
        "exit_deviation_percent": exit_deviation_percent,
        "min_session_bars": _require_positive_int_like(
            normalized["min_session_bars"], f"{label} min_session_bars"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_opening_gap_fade_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "min_gap_percent",
            "exit_gap_fill_percent",
            "min_session_bars",
            "confirmation_bars",
        ],
        label,
    )
    min_gap_percent = _require_non_negative_float_like(
        normalized["min_gap_percent"], f"{label} min_gap_percent"
    )
    exit_gap_fill_percent = _require_non_negative_float_like(
        normalized["exit_gap_fill_percent"], f"{label} exit_gap_fill_percent"
    )
    if min_gap_percent == 0.0:
        raise ValueError(f"{label} min_gap_percent must be > 0")
    if exit_gap_fill_percent > 1.0:
        raise ValueError(f"{label} exit_gap_fill_percent must be <= 1")
    return {
        "min_gap_percent": min_gap_percent,
        "exit_gap_fill_percent": exit_gap_fill_percent,
        "min_session_bars": _require_positive_int_like(
            normalized["min_session_bars"], f"{label} min_session_bars"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_ornstein_uhlenbeck_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "window",
            "entry_sigma",
            "exit_sigma",
            "min_mean_reversion_speed",
            "confirmation_bars",
        ],
        label,
    )
    entry_sigma = _require_non_negative_float_like(
        normalized["entry_sigma"], f"{label} entry_sigma"
    )
    exit_sigma = _require_non_negative_float_like(
        normalized["exit_sigma"], f"{label} exit_sigma"
    )
    min_mean_reversion_speed = _require_non_negative_float_like(
        normalized["min_mean_reversion_speed"],
        f"{label} min_mean_reversion_speed",
    )
    if entry_sigma == 0.0:
        raise ValueError(f"{label} entry_sigma must be > 0")
    if exit_sigma > entry_sigma:
        raise ValueError(f"{label} requires exit_sigma <= entry_sigma")
    return {
        "window": _require_positive_int_like(normalized["window"], f"{label} window"),
        "entry_sigma": entry_sigma,
        "exit_sigma": exit_sigma,
        "min_mean_reversion_speed": min_mean_reversion_speed,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_volatility_breakout_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "atr_window",
            "compression_window",
            "compression_threshold",
            "breakout_lookback",
            "breakout_buffer",
            "confirmation_bars",
        ],
        label,
    )
    compression_threshold = _require_non_negative_float_like(
        normalized["compression_threshold"], f"{label} compression_threshold"
    )
    if compression_threshold == 0.0:
        raise ValueError(f"{label} compression_threshold must be > 0")
    return {
        "atr_window": _require_positive_int_like(
            normalized["atr_window"], f"{label} atr_window"
        ),
        "compression_window": _require_positive_int_like(
            normalized["compression_window"], f"{label} compression_window"
        ),
        "compression_threshold": compression_threshold,
        "breakout_lookback": _require_positive_int_like(
            normalized["breakout_lookback"], f"{label} breakout_lookback"
        ),
        "breakout_buffer": _require_non_negative_float_like(
            normalized["breakout_buffer"], f"{label} breakout_buffer"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_atr_channel_breakout_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["channel_window", "atr_window", "atr_multiplier", "confirmation_bars"],
        label,
    )
    atr_multiplier = _require_non_negative_float_like(
        normalized["atr_multiplier"], f"{label} atr_multiplier"
    )
    if atr_multiplier == 0.0:
        raise ValueError(f"{label} atr_multiplier must be > 0")
    return {
        "channel_window": _require_positive_int_like(
            normalized["channel_window"], f"{label} channel_window"
        ),
        "atr_window": _require_positive_int_like(
            normalized["atr_window"], f"{label} atr_window"
        ),
        "atr_multiplier": atr_multiplier,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_volatility_mean_reversion_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "volatility_window",
            "baseline_window",
            "high_threshold",
            "low_threshold",
            "confirmation_bars",
        ],
        label,
    )
    high_threshold = _require_non_negative_float_like(
        normalized["high_threshold"], f"{label} high_threshold"
    )
    low_threshold = _require_non_negative_float_like(
        normalized["low_threshold"], f"{label} low_threshold"
    )
    if high_threshold <= 1.0:
        raise ValueError(f"{label} high_threshold must be > 1")
    if low_threshold <= 0.0 or low_threshold >= 1.0:
        raise ValueError(f"{label} low_threshold must be within (0, 1)")
    return {
        "volatility_window": _require_positive_int_like(
            normalized["volatility_window"], f"{label} volatility_window"
        ),
        "baseline_window": _require_positive_int_like(
            normalized["baseline_window"], f"{label} baseline_window"
        ),
        "high_threshold": high_threshold,
        "low_threshold": low_threshold,
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_support_resistance_bounce_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "level_window",
            "touch_tolerance",
            "rejection_min_close_delta",
            "confirmation_bars",
        ],
        label,
    )
    return {
        "level_window": _require_positive_int_like(
            normalized["level_window"], f"{label} level_window"
        ),
        "touch_tolerance": _require_non_negative_float_like(
            normalized["touch_tolerance"], f"{label} touch_tolerance"
        ),
        "rejection_min_close_delta": _require_non_negative_float_like(
            normalized["rejection_min_close_delta"],
            f"{label} rejection_min_close_delta",
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_breakout_retest_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "breakout_window",
            "breakout_buffer",
            "retest_tolerance",
            "confirmation_bars",
        ],
        label,
    )
    return {
        "breakout_window": _require_positive_int_like(
            normalized["breakout_window"], f"{label} breakout_window"
        ),
        "breakout_buffer": _require_non_negative_float_like(
            normalized["breakout_buffer"], f"{label} breakout_buffer"
        ),
        "retest_tolerance": _require_non_negative_float_like(
            normalized["retest_tolerance"], f"{label} retest_tolerance"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_pivot_point_strategy_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["pivot_lookback", "level_tolerance", "confirmation_bars"],
        label,
    )
    return {
        "pivot_lookback": _require_positive_int_like(
            normalized["pivot_lookback"], f"{label} pivot_lookback"
        ),
        "level_tolerance": _require_non_negative_float_like(
            normalized["level_tolerance"], f"{label} level_tolerance"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_opening_range_breakout_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["opening_range_minutes", "breakout_buffer", "confirmation_bars"],
        label,
    )
    return {
        "opening_range_minutes": _require_positive_int_like(
            normalized["opening_range_minutes"], f"{label} opening_range_minutes"
        ),
        "breakout_buffer": _require_non_negative_float_like(
            normalized["breakout_buffer"], f"{label} breakout_buffer"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_inside_bar_breakout_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["breakout_buffer", "confirmation_bars"],
        label,
    )
    return {
        "breakout_buffer": _require_non_negative_float_like(
            normalized["breakout_buffer"], f"{label} breakout_buffer"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_gap_and_go_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "gap_threshold",
            "continuation_threshold",
            "volume_window",
            "relative_volume_threshold",
            "confirmation_bars",
        ],
        label,
    )
    return {
        "gap_threshold": _require_non_negative_float_like(
            normalized["gap_threshold"], f"{label} gap_threshold"
        ),
        "continuation_threshold": _require_non_negative_float_like(
            normalized["continuation_threshold"],
            f"{label} continuation_threshold",
        ),
        "volume_window": _require_positive_int_like(
            normalized["volume_window"], f"{label} volume_window"
        ),
        "relative_volume_threshold": _require_non_negative_float_like(
            normalized["relative_volume_threshold"],
            f"{label} relative_volume_threshold",
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_trendline_break_strategy_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["trendline_window", "break_buffer", "slope_tolerance", "confirmation_bars"],
        label,
    )
    return {
        "trendline_window": _require_positive_int_like(
            normalized["trendline_window"], f"{label} trendline_window"
        ),
        "break_buffer": _require_non_negative_float_like(
            normalized["break_buffer"], f"{label} break_buffer"
        ),
        "slope_tolerance": _require_float_like(
            normalized["slope_tolerance"], f"{label} slope_tolerance"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def require_volatility_squeeze_breakout_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "squeeze_window",
            "bollinger_multiplier",
            "keltner_multiplier",
            "breakout_buffer",
            "confirmation_bars",
        ],
        label,
    )
    bollinger_multiplier = _require_non_negative_float_like(
        normalized["bollinger_multiplier"], f"{label} bollinger_multiplier"
    )
    keltner_multiplier = _require_non_negative_float_like(
        normalized["keltner_multiplier"], f"{label} keltner_multiplier"
    )
    if bollinger_multiplier == 0.0:
        raise ValueError(f"{label} bollinger_multiplier must be > 0")
    if keltner_multiplier == 0.0:
        raise ValueError(f"{label} keltner_multiplier must be > 0")
    return {
        "squeeze_window": _require_positive_int_like(
            normalized["squeeze_window"], f"{label} squeeze_window"
        ),
        "bollinger_multiplier": bollinger_multiplier,
        "keltner_multiplier": keltner_multiplier,
        "breakout_buffer": _require_non_negative_float_like(
            normalized["breakout_buffer"], f"{label} breakout_buffer"
        ),
        "confirmation_bars": _require_positive_int_like(
            normalized["confirmation_bars"], f"{label} confirmation_bars"
        ),
    }


def _require_rows_param(raw_rows, label):
    if not isinstance(raw_rows, list):
        raise ValueError(f"{label} rows must be a list")
    normalized_rows = []
    for index, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} rows[{index}] must be a dict")
        child_outputs = row.get("child_outputs")
        if not isinstance(child_outputs, list):
            raise ValueError(f"{label} rows[{index}] child_outputs must be a list")
        normalized_rows.append(dict(row))
    return normalized_rows


def _require_dict_rows(raw_rows, label):
    if not isinstance(raw_rows, list):
        raise ValueError(f"{label} rows must be a list")
    normalized_rows = []
    for index, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} rows[{index}] must be a dict")
        normalized_rows.append(dict(row))
    return normalized_rows


def _require_string_float_dict(value, label):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a dict")
    return {
        _require_non_empty_string(key, f"{label} key"): _require_float_like(
            raw_value, f"{label}[{key}]"
        )
        for key, raw_value in value.items()
    }


def _require_cross_sectional_rows_param(raw_rows, label):
    if not isinstance(raw_rows, list):
        raise ValueError(f"{label} rows must be a list")
    normalized_rows = []
    for index, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} rows[{index}] must be a dict")
        if row.get("symbol") in [None, ""]:
            raise ValueError(f"{label} rows[{index}] symbol is required")
        if row.get("ts") is None and row.get("timestamp") is None:
            raise ValueError(f"{label} rows[{index}] timestamp is required")
        if row.get("Close") is None and row.get("close") is None:
            raise ValueError(f"{label} rows[{index}] close is required")
        normalized_rows.append(dict(row))
    return normalized_rows


def require_cross_sectional_momentum_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["rows", "lookback_window", "top_n", "rebalance_frequency", "long_only"],
        label,
    )
    lookback_window = _require_positive_int_like(
        normalized["lookback_window"], f"{label} lookback_window"
    )
    top_n = _require_positive_int_like(normalized["top_n"], f"{label} top_n")
    bottom_n = _require_int_like(normalized.get("bottom_n", 0), f"{label} bottom_n")
    if bottom_n < 0:
        raise ValueError(f"{label} bottom_n must be >= 0")
    long_only = _normalize_bool_like(normalized["long_only"], f"{label} long_only")
    if long_only and bottom_n != 0:
        raise ValueError(f"{label} bottom_n must be 0 when long_only is true")
    rebalance_frequency = _require_choice(
        normalized["rebalance_frequency"],
        f"{label} rebalance_frequency",
        allowed={"monthly", "weekly", "all"},
    )
    result = {
        "rows": _require_cross_sectional_rows_param(normalized["rows"], label),
        "lookback_window": lookback_window,
        "top_n": top_n,
        "bottom_n": bottom_n,
        "rebalance_frequency": rebalance_frequency,
        "long_only": long_only,
        "score_adjustments": _require_string_float_dict(
            normalized.get("score_adjustments"), f"{label} score_adjustments"
        ),
    }
    absolute_threshold = normalized.get("absolute_momentum_threshold")
    if absolute_threshold is not None:
        result["absolute_momentum_threshold"] = _require_float_like(
            absolute_threshold, f"{label} absolute_momentum_threshold"
        )
    defensive_symbol = normalized.get("defensive_symbol")
    if defensive_symbol is not None:
        result["defensive_symbol"] = _require_non_empty_string(
            defensive_symbol, f"{label} defensive_symbol"
        )
    return result


def require_factor_portfolio_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "field_names",
            "rebalance_frequency",
            "top_n",
            "long_only",
            "minimum_universe_size",
        ],
        label,
    )
    top_n = _require_positive_int_like(normalized["top_n"], f"{label} top_n")
    bottom_n = _require_int_like(normalized.get("bottom_n", 0), f"{label} bottom_n")
    if bottom_n < 0:
        raise ValueError(f"{label} bottom_n must be >= 0")
    long_only = _normalize_bool_like(normalized["long_only"], f"{label} long_only")
    if long_only and bottom_n != 0:
        raise ValueError(f"{label} bottom_n must be 0 when long_only is true")
    result = {
        "rows": _require_cross_sectional_rows_param(normalized["rows"], label),
        "field_names": _require_non_empty_string_list(
            normalized["field_names"], f"{label} field_names"
        ),
        "rebalance_frequency": _require_choice(
            normalized["rebalance_frequency"],
            f"{label} rebalance_frequency",
            allowed={"monthly", "weekly", "all"},
        ),
        "top_n": top_n,
        "bottom_n": bottom_n,
        "long_only": long_only,
        "minimum_universe_size": _require_positive_int_like(
            normalized["minimum_universe_size"], f"{label} minimum_universe_size"
        ),
    }
    weighting_mode = normalized.get("weighting_mode")
    if weighting_mode is not None:
        result["weighting_mode"] = _require_choice(
            weighting_mode,
            f"{label} weighting_mode",
            allowed={"equal_weight", "inverse_metric"},
        )
    target_value = normalized.get("target_value")
    if target_value is not None:
        result["target_value"] = _require_float_like(
            target_value,
            f"{label} target_value",
        )
    field_weights = normalized.get("field_weights")
    if field_weights is not None:
        normalized_field_weights = _require_positive_float_list(
            field_weights,
            f"{label} field_weights",
            minimum_length=1,
        )
        if len(normalized_field_weights) != len(result["field_names"]):
            raise ValueError(f"{label} field_weights must match field_names length")
        result["field_weights"] = normalized_field_weights
    lower_is_better_fields = normalized.get("lower_is_better_fields")
    if lower_is_better_fields is not None:
        normalized_lower_fields = _require_non_empty_string_list(
            lower_is_better_fields,
            f"{label} lower_is_better_fields",
        )
        invalid_fields = sorted(
            set(normalized_lower_fields).difference(result["field_names"])
        )
        if invalid_fields:
            raise ValueError(
                f"{label} lower_is_better_fields must be a subset of field_names"
            )
        result["lower_is_better_fields"] = normalized_lower_fields
    for optional_threshold_key in (
        "sentiment_threshold",
        "classification_threshold",
        "return_threshold",
        "regime_threshold",
        "vote_threshold",
    ):
        optional_threshold_value = normalized.get(optional_threshold_key)
        if optional_threshold_value is not None:
            result[optional_threshold_key] = _require_float_like(
                optional_threshold_value,
                f"{label} {optional_threshold_key}",
            )
    return result


def require_cross_asset_ranking_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "field_names",
            "rebalance_frequency",
            "top_n",
            "long_only",
            "minimum_universe_size",
        ],
        label,
    )
    top_n = _require_positive_int_like(normalized["top_n"], f"{label} top_n")
    bottom_n = _require_int_like(normalized.get("bottom_n", 0), f"{label} bottom_n")
    if bottom_n < 0:
        raise ValueError(f"{label} bottom_n must be >= 0")
    long_only = _normalize_bool_like(normalized["long_only"], f"{label} long_only")
    if long_only and bottom_n != 0:
        raise ValueError(f"{label} bottom_n must be 0 when long_only is true")
    return {
        "rows": _require_cross_sectional_rows_param(normalized["rows"], label),
        "field_names": _require_non_empty_string_list(
            normalized["field_names"], f"{label} field_names"
        ),
        "rebalance_frequency": _require_choice(
            normalized["rebalance_frequency"],
            f"{label} rebalance_frequency",
            allowed={"monthly", "weekly", "all"},
        ),
        "top_n": top_n,
        "bottom_n": bottom_n,
        "long_only": long_only,
        "minimum_universe_size": _require_positive_int_like(
            normalized["minimum_universe_size"], f"{label} minimum_universe_size"
        ),
    }


def require_multi_leg_rebalance_param(raw_alg_param, label):
    normalized = require_cross_asset_ranking_param(raw_alg_param, label)
    return {
        **normalized,
        "front_leg_field": _require_non_empty_string(
            raw_alg_param.get("front_leg_field"), f"{label} front_leg_field"
        ),
        "back_leg_field": _require_non_empty_string(
            raw_alg_param.get("back_leg_field"), f"{label} back_leg_field"
        ),
    }


def require_seasonality_calendar_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["rows", "rebalance_frequency", "top_n", "long_only", "minimum_universe_size"],
        label,
    )
    top_n = _require_positive_int_like(normalized["top_n"], f"{label} top_n")
    bottom_n = _require_int_like(normalized.get("bottom_n", 0), f"{label} bottom_n")
    if bottom_n < 0:
        raise ValueError(f"{label} bottom_n must be >= 0")
    long_only = _normalize_bool_like(normalized["long_only"], f"{label} long_only")
    if long_only and bottom_n != 0:
        raise ValueError(f"{label} bottom_n must be 0 when long_only is true")
    result = {
        "rows": _require_cross_sectional_rows_param(normalized["rows"], label),
        "rebalance_frequency": _require_choice(
            normalized["rebalance_frequency"],
            f"{label} rebalance_frequency",
            allowed={"monthly", "weekly", "all"},
        ),
        "top_n": top_n,
        "bottom_n": bottom_n,
        "long_only": long_only,
        "minimum_universe_size": _require_positive_int_like(
            normalized["minimum_universe_size"], f"{label} minimum_universe_size"
        ),
    }
    result["calendar_pattern"] = _require_choice(
        normalized.get("calendar_pattern", "turn_of_month"),
        f"{label} calendar_pattern",
        allowed={"turn_of_month", "month_end", "monday", "friday"},
    )
    return result


def require_event_driven_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "event_rows",
            "rebalance_frequency",
            "top_n",
            "long_only",
            "minimum_universe_size",
            "post_event_window_days",
        ],
        label,
    )
    result = require_cross_asset_ranking_param(normalized, label)
    event_rows = normalized["event_rows"]
    if not isinstance(event_rows, list):
        raise ValueError(f"{label} event_rows must be a list")
    normalized_events: list[dict[str, object]] = []
    for index, row in enumerate(event_rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} event_rows[{index}] must be a dict")
        if row.get("symbol") in (None, ""):
            raise ValueError(f"{label} event_rows[{index}] symbol is required")
        if row.get("event_timestamp") in (None, ""):
            raise ValueError(f"{label} event_rows[{index}] event_timestamp is required")
        normalized_events.append(dict(row))
    result["event_rows"] = normalized_events
    result["post_event_window_days"] = _require_positive_int_like(
        normalized["post_event_window_days"], f"{label} post_event_window_days"
    )
    result["surprise_field"] = _require_non_empty_string(
        normalized.get("surprise_field", "surprise"), f"{label} surprise_field"
    )
    return result


def require_single_asset_event_window_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["rows", "event_rows", "event_value_field"],
        label,
    )
    result = {
        "rows": _require_cross_sectional_rows_param(normalized["rows"], label),
        "event_value_field": _require_non_empty_string(
            normalized["event_value_field"], f"{label} event_value_field"
        ),
        "pre_event_window_days": _require_int_like(
            normalized.get("pre_event_window_days", 0),
            f"{label} pre_event_window_days",
        ),
        "post_event_window_days": _require_int_like(
            normalized.get("post_event_window_days", 0),
            f"{label} post_event_window_days",
        ),
        "bullish_phase": _require_choice(
            normalized.get("bullish_phase", "post_event"),
            f"{label} bullish_phase",
            allowed={"pre_event", "post_event"},
        ),
        "minimum_score_threshold": _require_non_negative_float_like(
            normalized.get("minimum_score_threshold", 0.0),
            f"{label} minimum_score_threshold",
        ),
    }
    if result["pre_event_window_days"] < 0:
        raise ValueError(f"{label} pre_event_window_days must be >= 0")
    if result["post_event_window_days"] < 0:
        raise ValueError(f"{label} post_event_window_days must be >= 0")
    event_rows = normalized["event_rows"]
    if not isinstance(event_rows, list):
        raise ValueError(f"{label} event_rows must be a list")
    normalized_events: list[dict[str, object]] = []
    for index, row in enumerate(event_rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} event_rows[{index}] must be a dict")
        if row.get("symbol") in (None, ""):
            raise ValueError(f"{label} event_rows[{index}] symbol is required")
        if row.get("event_timestamp") in (None, ""):
            raise ValueError(f"{label} event_rows[{index}] event_timestamp is required")
        normalized_events.append(dict(row))
    result["event_rows"] = normalized_events
    expected_direction_field = normalized.get("expected_direction_field")
    if expected_direction_field is not None:
        result["expected_direction_field"] = _require_non_empty_string(
            expected_direction_field, f"{label} expected_direction_field"
        )
    return result


def _require_float_like(value, label):
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"{label} must be a number: {exc}")


def require_hard_boolean_gating_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["mode", "tie_policy", "veto_sell_count", "rows"],
        label,
    )
    veto_sell_count = _require_int_like(
        normalized["veto_sell_count"], f"{label} veto_sell_count"
    )
    if veto_sell_count < 0:
        raise ValueError(f"{label} veto_sell_count must be >= 0")
    result = {
        "mode": _require_choice(
            normalized["mode"],
            f"{label} mode",
            allowed={"and", "or", "majority"},
        ),
        "tie_policy": _require_choice(
            normalized["tie_policy"],
            f"{label} tie_policy",
            allowed={"neutral", "buy", "sell"},
        ),
        "veto_sell_count": veto_sell_count,
        "rows": _require_dict_rows(normalized["rows"], label),
    }
    if normalized.get("expected_child_count") is not None:
        result["expected_child_count"] = _require_positive_int_like(
            normalized["expected_child_count"], f"{label} expected_child_count"
        )
    return result


def require_weighted_linear_score_blend_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["weights", "buy_threshold", "sell_threshold", "rows"],
        label,
    )
    raw_weights = normalized["weights"]
    if not isinstance(raw_weights, dict):
        raise ValueError(f"{label} weights must be a dict")
    weights = {
        _require_non_empty_string(key, f"{label} weights key"): _require_float_like(
            value, f"{label} weights[{key}]"
        )
        for key, value in raw_weights.items()
    }
    if not weights:
        raise ValueError(f"{label} weights must not be empty")
    buy_threshold = _require_float_like(
        normalized["buy_threshold"], f"{label} buy_threshold"
    )
    sell_threshold = _require_float_like(
        normalized["sell_threshold"], f"{label} sell_threshold"
    )
    if sell_threshold > buy_threshold:
        raise ValueError(f"{label} requires sell_threshold <= buy_threshold")
    result = {
        "weights": weights,
        "buy_threshold": buy_threshold,
        "sell_threshold": sell_threshold,
        "rows": _require_dict_rows(normalized["rows"], label),
    }
    if normalized.get("expected_child_count") is not None:
        result["expected_child_count"] = _require_positive_int_like(
            normalized["expected_child_count"], f"{label} expected_child_count"
        )
    return result


def require_rank_aggregation_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "aggregation_method",
            "rank_field_names",
            "top_k",
            "minimum_child_count",
        ],
        label,
    )
    rank_field_names = _require_non_empty_string_list(
        normalized["rank_field_names"], f"{label} rank_field_names"
    )
    score_field_names = normalized.get("score_field_names", [])
    if not isinstance(score_field_names, list):
        raise ValueError(f"{label} score_field_names must be a list")
    return {
        "rows": _require_dict_rows(normalized["rows"], label),
        "aggregation_method": _require_choice(
            normalized["aggregation_method"],
            f"{label} aggregation_method",
            allowed={"average_rank", "median_rank"},
        ),
        "rank_field_names": rank_field_names,
        "score_field_names": [
            _require_non_empty_string(item, f"{label} score_field_names[{index}]")
            for index, item in enumerate(score_field_names)
        ],
        "top_k": _require_positive_int_like(normalized["top_k"], f"{label} top_k"),
        "minimum_child_count": _require_positive_int_like(
            normalized["minimum_child_count"], f"{label} minimum_child_count"
        ),
    }


def require_risk_budgeting_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        ["rows", "rebalance_frequency", "target_gross_exposure", "min_history"],
        label,
    )
    target_gross_exposure = _require_non_negative_float_like(
        normalized["target_gross_exposure"], f"{label} target_gross_exposure"
    )
    if target_gross_exposure == 0.0:
        raise ValueError(f"{label} target_gross_exposure must be > 0")
    return {
        "rows": _require_rows_param(normalized["rows"], label),
        "rebalance_frequency": _require_choice(
            normalized["rebalance_frequency"],
            f"{label} rebalance_frequency",
            allowed={"monthly", "weekly", "all"},
        ),
        "target_gross_exposure": target_gross_exposure,
        "min_history": _require_positive_int_like(
            normalized["min_history"], f"{label} min_history"
        ),
    }


def require_volatility_targeting_overlay_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "target_volatility",
            "base_weight",
            "min_history",
            "max_leverage",
            "min_leverage",
        ],
        label,
    )
    target_volatility = _require_non_negative_float_like(
        normalized["target_volatility"], f"{label} target_volatility"
    )
    base_weight = _require_non_negative_float_like(
        normalized["base_weight"], f"{label} base_weight"
    )
    max_leverage = _require_non_negative_float_like(
        normalized["max_leverage"], f"{label} max_leverage"
    )
    min_leverage = _require_non_negative_float_like(
        normalized["min_leverage"], f"{label} min_leverage"
    )
    if target_volatility == 0.0:
        raise ValueError(f"{label} target_volatility must be > 0")
    if base_weight == 0.0:
        raise ValueError(f"{label} base_weight must be > 0")
    if max_leverage < min_leverage:
        raise ValueError(f"{label} requires max_leverage >= min_leverage")
    return {
        "rows": _require_rows_param(normalized["rows"], label),
        "target_volatility": target_volatility,
        "base_weight": base_weight,
        "min_history": _require_positive_int_like(
            normalized["min_history"], f"{label} min_history"
        ),
        "max_leverage": max_leverage,
        "min_leverage": min_leverage,
    }


def require_constrained_multi_factor_optimization_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "rebalance_frequency",
            "target_gross_exposure",
            "min_history",
            "max_weight",
        ],
        label,
    )
    target_gross_exposure = _require_non_negative_float_like(
        normalized["target_gross_exposure"], f"{label} target_gross_exposure"
    )
    max_weight = _require_non_negative_float_like(
        normalized["max_weight"], f"{label} max_weight"
    )
    if target_gross_exposure == 0.0:
        raise ValueError(f"{label} target_gross_exposure must be > 0")
    if max_weight == 0.0:
        raise ValueError(f"{label} max_weight must be > 0")
    return {
        "rows": _require_rows_param(normalized["rows"], label),
        "rebalance_frequency": _require_choice(
            normalized["rebalance_frequency"],
            f"{label} rebalance_frequency",
            allowed={"monthly", "weekly", "all"},
        ),
        "target_gross_exposure": target_gross_exposure,
        "min_history": _require_positive_int_like(
            normalized["min_history"], f"{label} min_history"
        ),
        "max_weight": max_weight,
    }


def require_regime_switching_hmm_gating_param(raw_alg_param, label):
    normalized = _require_param_dict(raw_alg_param, label)
    _validate_required_keys(
        normalized,
        [
            "rows",
            "regime_field",
            "regime_map",
            "smoothing",
            "switch_threshold",
        ],
        label,
    )
    regime_map = normalized["regime_map"]
    if not isinstance(regime_map, dict):
        raise ValueError(f"{label} regime_map must be a dict")
    normalized_map: dict[str, list[str]] = {}
    for regime_label, child_keys in regime_map.items():
        if not isinstance(child_keys, list):
            raise ValueError(f"{label} regime_map[{regime_label}] must be a list")
        normalized_map[
            _require_non_empty_string(regime_label, f"{label} regime_map key")
        ] = [
            _require_non_empty_string(
                child_key,
                f"{label} regime_map[{regime_label}][{index}]",
            )
            for index, child_key in enumerate(child_keys)
        ]
    return {
        "rows": _require_dict_rows(normalized["rows"], label),
        "regime_field": _require_non_empty_string(
            normalized["regime_field"], f"{label} regime_field"
        ),
        "regime_map": normalized_map,
        "default_signal": _require_choice(
            normalized.get("default_signal", "neutral"),
            f"{label} default_signal",
            allowed={"buy", "sell", "neutral"},
        ),
        "smoothing": _require_non_negative_float_like(
            normalized["smoothing"], f"{label} smoothing"
        ),
        "switch_threshold": _require_non_negative_float_like(
            normalized["switch_threshold"], f"{label} switch_threshold"
        ),
        "expected_child_count": _require_positive_int_like(
            normalized.get("expected_child_count", 1),
            f"{label} expected_child_count",
        ),
    }


def normalize_alertgen_sensor_config(
    sensor_config, label="Alert generator sensor_config"
):
    if not isinstance(sensor_config, dict):
        raise ValueError(f"{label} must be a dict/JSON object")
    normalized = dict(sensor_config)
    _validate_required_keys(normalized, ["buy", "sell", "symbol"], label)
    normalized["buy"] = _normalize_bool_like(normalized["buy"], f"{label} buy")
    normalized["sell"] = _normalize_bool_like(normalized["sell"], f"{label} sell")
    if normalized["buy"] is False and normalized["sell"] is False:
        raise ValueError(f"{label} requires at least one of buy/sell to be enabled")
    normalized["symbol"] = _require_non_empty_string(
        normalized["symbol"], f"{label} symbol", reject_random_name=True
    )
    if normalized.get("configuration_payload") is not None:
        from trading_algos.configuration.serialization import configuration_from_dict
        from trading_algos.configuration.validation import (
            validate_configuration_payload,
        )

        raw_configuration_payload = normalized["configuration_payload"]
        if isinstance(raw_configuration_payload, str):
            raw_configuration_payload = json.loads(raw_configuration_payload)
        if not isinstance(raw_configuration_payload, dict):
            raise ValueError(
                f"{label} configuration_payload must be a dict/JSON object"
            )
        configuration = validate_configuration_payload(
            configuration_from_dict(raw_configuration_payload)
        )
        normalized["configuration_payload"] = configuration.to_dict()
        normalized["alg_key"] = f"config:{configuration.config_key}"
        normalized["alg_param"] = {"version": configuration.version}
        return normalized
    _validate_required_keys(normalized, ["alg_param", "alg_key"], label)
    normalized["alg_key"] = _require_non_empty_string(
        normalized["alg_key"], f"{label} alg_key"
    )
    normalized["alg_param"] = _normalize_alertgen_alg_param(
        alg_key=normalized["alg_key"],
        raw_alg_param=normalized["alg_param"],
        label=f"{label} alg_param",
    )
    return normalized
