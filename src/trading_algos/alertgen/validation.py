import json


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


def _validate_unique_sensor_names(sensors, label_prefix="Alert generator"):
    seen_names = set()
    for idx, sensor in enumerate(sensors):
        sensor_name = sensor["name"]
        if not isinstance(sensor_name, str) or not sensor_name.strip():
            raise ValueError(f"{label_prefix} sensor #{idx + 1} name is required.")
        normalized_name = sensor_name.strip().casefold()
        if normalized_name in seen_names:
            raise ValueError(f"{label_prefix} sensor names must be unique.")
        seen_names.add(normalized_name)


def _normalize_alertgen_engine_type(engine_type, label):
    normalized = _require_non_empty_string(engine_type, label)
    supported_types = {"gen1"}
    if normalized not in supported_types:
        raise ValueError(
            f"{label} must be one of: {', '.join(sorted(supported_types))}"
        )
    return normalized


def _normalize_alertgen_alg_param(alg_code, raw_alg_param, label):
    if alg_code in [100, 101, 102]:
        return _require_int_like(raw_alg_param, label)
    if alg_code in [200, 201, 901]:
        return _require_positive_int_like(raw_alg_param, label)
    if alg_code == 902:
        if not isinstance(raw_alg_param, list) or len(raw_alg_param) != 2:
            raise ValueError(f"{label} must be a list of length 2")
        return [_require_positive_int_like(item, label) for item in raw_alg_param]
    raise ValueError(f"sensor_config alg_code={alg_code} is unsupported")


def normalize_alertgen_sensor_config(
    sensor_config, label="Alert generator sensor_config"
):
    if not isinstance(sensor_config, dict):
        raise ValueError(f"{label} must be a dict/JSON object")
    normalized = dict(sensor_config)
    _validate_required_keys(
        normalized, ["buy", "sell", "alg_code", "symbol", "alg_param"], label
    )
    normalized["buy"] = _normalize_bool_like(normalized["buy"], f"{label} buy")
    normalized["sell"] = _normalize_bool_like(normalized["sell"], f"{label} sell")
    if normalized["buy"] is False and normalized["sell"] is False:
        raise ValueError(f"{label} requires at least one of buy/sell to be enabled")
    normalized["symbol"] = _require_non_empty_string(
        normalized["symbol"], f"{label} symbol", reject_random_name=True
    )
    normalized["alg_code"] = _require_int_like(
        normalized["alg_code"], f"{label} alg_code"
    )
    normalized["alg_param"] = _normalize_alertgen_alg_param(
        normalized["alg_code"], normalized["alg_param"], f"{label} alg_param"
    )
    return normalized


def validate_alertgen_engine_payload(payload, label="Alert generator"):
    if not isinstance(payload, dict):
        raise ValueError(f"{label} config must be a dict/JSON object")
    normalized = dict(payload)
    _validate_required_keys(
        normalized, ["name", "engine_config", "enable", "sensors"], f"{label} config"
    )
    normalized["name"] = _require_non_empty_string(normalized["name"], f"{label} name")
    normalized["enable"] = bool(normalized["enable"])

    engine_config = _require_json_object_dict(
        normalized["engine_config"], f"{label} engine_config"
    )
    _validate_required_keys(
        engine_config, ["type", "interval_secs"], f"{label} engine_config"
    )
    try:
        engine_config["interval_secs"] = int(engine_config["interval_secs"])
    except Exception as exc:
        raise ValueError(
            f"{label} engine_config interval_secs must be an integer: {exc}"
        )
    if engine_config["interval_secs"] <= 0:
        raise ValueError(f"{label} engine_config interval_secs must be > 0")
    engine_config["type"] = _normalize_alertgen_engine_type(
        engine_config["type"], f"{label} engine_config type"
    )
    normalized["engine_config"] = engine_config

    sensors = normalized["sensors"]
    if not isinstance(sensors, list) or len(sensors) == 0:
        raise ValueError(f"{label} sensors must be a non-empty list")
    _validate_unique_sensor_names(sensors, label_prefix=label)

    normalized_sensors = []
    for idx, sensor in enumerate(sensors):
        if not isinstance(sensor, dict):
            raise ValueError(f"sensor #{idx + 1} must be a dict/JSON object")
        _validate_required_keys(
            sensor, ["name", "sensor_config", "enable"], f"sensor #{idx + 1}"
        )
        sensor_config = _require_json_object_dict(
            sensor["sensor_config"], f"sensor #{idx + 1} sensor_config"
        )
        normalized_sensors.append(
            {
                "name": _require_non_empty_string(
                    sensor["name"], f"{label} sensor #{idx + 1} name"
                ),
                "sensor_config": normalize_alertgen_sensor_config(
                    sensor_config, label=f"sensor #{idx + 1} sensor_config"
                ),
                "enable": bool(sensor["enable"]),
            }
        )

    normalized["sensors"] = normalized_sensors
    return normalized
