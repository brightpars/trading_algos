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
        "rows": _require_rows_param(normalized["rows"], label),
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
        "rows": _require_rows_param(normalized["rows"], label),
    }
    if normalized.get("expected_child_count") is not None:
        result["expected_child_count"] = _require_positive_int_like(
            normalized["expected_child_count"], f"{label} expected_child_count"
        )
    return result


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
