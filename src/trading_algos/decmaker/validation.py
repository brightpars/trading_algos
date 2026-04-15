def _validate_required_keys(payload, required_keys, label):
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing_keys)}")


def validate_decmaker_engine_payload(payload, label="Decision maker engine config"):
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a dict/JSON object")
    normalized = dict(payload)
    _validate_required_keys(
        normalized,
        [
            "type",
            "interval_secs",
            "confidence_threshold_buy",
            "confidence_threshold_sell",
            "max_percent_higher_price_buy",
            "max_percent_lower_price_sell",
        ],
        label,
    )

    try:
        normalized["interval_secs"] = int(normalized["interval_secs"])
    except Exception as exc:
        raise ValueError(f"{label} interval_secs must be an integer: {exc}")
    if normalized["interval_secs"] <= 0:
        raise ValueError(f"{label} interval_secs must be > 0")

    if str(normalized["type"]).strip() != "dec1":
        raise ValueError(f"{label} type must be dec1")
    normalized["type"] = "dec1"

    for field_name in [
        "confidence_threshold_buy",
        "confidence_threshold_sell",
        "max_percent_higher_price_buy",
        "max_percent_lower_price_sell",
    ]:
        try:
            normalized[field_name] = float(normalized[field_name])
        except Exception as exc:
            raise ValueError(f"{label} field '{field_name}' must be numeric: {exc}")

    return normalized
