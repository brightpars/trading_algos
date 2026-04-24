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
