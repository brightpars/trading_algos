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
