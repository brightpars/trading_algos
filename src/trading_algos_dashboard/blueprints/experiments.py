from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from json import JSONDecodeError

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from trading_algos.configuration.validation import validate_configuration_payload
from trading_algos_dashboard.extensions import (
    clear_form_state,
    load_form_state,
    persist_form_state,
)

from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
    MarketDataUnavailableError,
)
from trading_algos_dashboard.services.single_algorithm_configuration import (
    build_single_algorithm_configuration_payload,
    extract_single_algorithm_from_configuration_payload,
)

bp = Blueprint("experiments", __name__, url_prefix="/experiments")

_EXPERIMENT_FORM_COOKIE = "trading_algos_dashboard_experiment_form"
_BULK_EXPERIMENT_FORM_COOKIE = "trading_algos_dashboard_bulk_experiment_form"


def _as_str_any_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _experiment_form_defaults(catalog: list[dict[str, object]]) -> dict[str, str]:
    runtime_settings = current_app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()
    default_algorithms = "[]"
    if catalog:
        default_algorithms = json.dumps(
            build_single_algorithm_configuration_payload(
                alg_key=str(catalog[0]["key"]),
                alg_param=_as_str_any_dict(catalog[0].get("default_param")),
            )
        )
    return {
        "run_mode": "configuration",
        "configuration_source": "quick_builder",
        "selected_draft_id": "",
        "quick_builder_alg_key": str(catalog[0]["key"]) if catalog else "",
        "quick_builder_buy_enabled": "true",
        "quick_builder_sell_enabled": "true",
        "symbol": "",
        "start_date": "",
        "start_time": "09:30",
        "end_date": "",
        "end_time": "16:00",
        "configuration_json": default_algorithms,
        "alertgens_json": default_algorithms,
        "decmaker_key": "alg1",
        "engine_alertgen_count": "1",
        "decmaker_param_json": json.dumps(
            {
                "confidence_threshold_buy": 0.6,
                "confidence_threshold_sell": 0.6,
                "max_percent_higher_price_buy": 0.0,
                "max_percent_lower_price_sell": 0.0,
            }
        ),
        "speed_factor": "60",
        "notes": "",
        "max_concurrent_experiments": str(
            runtime_settings["max_concurrent_experiments"]
        )
        if current_app
        else "1",
    }


def _supports_quick_builder_algorithm(spec: dict[str, object]) -> bool:
    default_param = spec.get("default_param")
    param_schema = spec.get("param_schema")
    if not isinstance(default_param, dict) or not isinstance(param_schema, list):
        return False

    supported_types = {"integer", "number", "string", "boolean"}
    for item in param_schema:
        if not isinstance(item, dict):
            return False
        key = item.get("key")
        param_type = item.get("type")
        if not isinstance(key, str) or key not in default_param:
            return False
        if param_type not in supported_types:
            return False
    return True


def _build_quick_builder_algorithms(
    catalog: list[dict[str, object]],
) -> list[dict[str, object]]:
    quick_builder_algorithms: list[dict[str, object]] = []
    for spec in catalog:
        if not _supports_quick_builder_algorithm(spec):
            continue
        default_param = spec.get("default_param")
        if not isinstance(default_param, dict):
            default_param = {}
        raw_param_schema = spec.get("param_schema")
        if not isinstance(raw_param_schema, list):
            raw_param_schema = []
        quick_builder_algorithms.append(
            {
                "key": str(spec.get("key", "")),
                "name": str(spec.get("name", "")),
                "description": str(spec.get("description", "")),
                "default_param": dict(default_param),
                "param_schema": [
                    dict(item) for item in raw_param_schema if isinstance(item, dict)
                ],
            }
        )
    return sorted(quick_builder_algorithms, key=lambda item: str(item["name"]))


def _supports_engine_chain_algorithm(spec: dict[str, object]) -> bool:
    if str(spec.get("status", "")) not in {"stable", "runnable"}:
        return False
    default_param = spec.get("default_param")
    param_schema = spec.get("param_schema")
    if not isinstance(default_param, dict) or not isinstance(param_schema, list):
        return False

    supported_types = {"integer", "number", "string", "boolean"}
    for item in param_schema:
        if not isinstance(item, dict):
            return False
        key = item.get("key")
        param_type = item.get("type")
        if not isinstance(key, str) or key not in default_param:
            return False
        if param_type not in supported_types:
            return False
    return True


def _build_engine_chain_algorithms(
    catalog: list[dict[str, object]],
) -> list[dict[str, object]]:
    engine_chain_algorithms: list[dict[str, object]] = []
    for spec in catalog:
        if not _supports_engine_chain_algorithm(spec):
            continue
        default_param = spec.get("default_param")
        raw_param_schema = spec.get("param_schema")
        if not isinstance(default_param, dict) or not isinstance(
            raw_param_schema, list
        ):
            continue
        engine_chain_algorithms.append(
            {
                "key": str(spec.get("key", "")),
                "name": str(spec.get("name", "")),
                "description": str(spec.get("description", "")),
                "default_param": dict(default_param),
                "param_schema": [
                    dict(item) for item in raw_param_schema if isinstance(item, dict)
                ],
            }
        )
    return sorted(engine_chain_algorithms, key=lambda item: str(item["name"]))


def _decmaker_param_schema(default_param: dict[str, object]) -> list[dict[str, object]]:
    schema: list[dict[str, object]] = []
    for key, value in default_param.items():
        if isinstance(value, bool):
            param_type = "boolean"
        elif isinstance(value, int) and not isinstance(value, bool):
            param_type = "integer"
        elif isinstance(value, float):
            param_type = "number"
        else:
            param_type = "string"
        schema.append(
            {
                "key": str(key),
                "label": str(key).replace("_", " ").title(),
                "type": param_type,
                "required": True,
            }
        )
    return schema


def _build_engine_chain_decmakers(
    decmakers: list[dict[str, object]],
) -> list[dict[str, object]]:
    engine_chain_decmakers: list[dict[str, object]] = []
    for decmaker in decmakers:
        default_param = decmaker.get("default_param")
        if not isinstance(default_param, dict):
            default_param = {}
        engine_chain_decmakers.append(
            {
                "key": str(decmaker.get("key", "")),
                "label": str(decmaker.get("label") or decmaker.get("name") or ""),
                "default_param": dict(default_param),
                "param_schema": _decmaker_param_schema(default_param),
            }
        )
    return sorted(engine_chain_decmakers, key=lambda item: str(item["label"]))


def _merge_engine_chain_defaults(
    engine_chain_algorithms: list[dict[str, object]],
    engine_chain_decmakers: list[dict[str, object]],
    form_data: dict[str, str],
) -> None:
    parsed_alertgens: list[dict[str, object]] = []
    try:
        raw_alertgens = json.loads(form_data.get("alertgens_json", "[]"))
    except JSONDecodeError:
        raw_alertgens = []
    if isinstance(raw_alertgens, list):
        parsed_alertgens = [item for item in raw_alertgens if isinstance(item, dict)]

    indices = _engine_alertgen_indices(form_data, parsed_alertgens)
    form_data["engine_alertgen_count"] = str(len(indices))
    form_data["engine_alertgen_order"] = json.dumps(indices)

    default_algorithm = engine_chain_algorithms[0] if engine_chain_algorithms else None
    algorithms_by_key = {
        str(item["key"]): item for item in engine_chain_algorithms if "key" in item
    }
    for position, index in enumerate(indices, start=1):
        form_key = f"engine_alertgen_{index}_alg_key"
        parsed_alertgen = (
            parsed_alertgens[position - 1]
            if position <= len(parsed_alertgens)
            else None
        )
        if form_data.get(form_key, "").strip() == "" and isinstance(
            parsed_alertgen, dict
        ):
            form_data[form_key] = str(parsed_alertgen.get("alg_key", ""))
        selected_algorithm = algorithms_by_key.get(
            form_data.get(form_key, ""), default_algorithm
        )
        if selected_algorithm is None:
            form_data[form_key] = ""
            continue
        form_data[form_key] = str(selected_algorithm["key"])
        default_param = selected_algorithm.get("default_param", {})
        if not isinstance(default_param, dict):
            default_param = {}
        parsed_alg_param = (
            parsed_alertgen.get("alg_param", {})
            if isinstance(parsed_alertgen, dict)
            else {}
        )
        if not isinstance(parsed_alg_param, dict):
            parsed_alg_param = {}
        for key, value in default_param.items():
            param_form_key = f"engine_alertgen_{index}_param__{key}"
            if param_form_key in form_data:
                continue
            if key in parsed_alg_param:
                parsed_value = parsed_alg_param[key]
                form_data[param_form_key] = (
                    json.dumps(parsed_value)
                    if isinstance(parsed_value, bool)
                    else str(parsed_value)
                )
                continue
            form_data[param_form_key] = (
                json.dumps(value) if isinstance(value, bool) else str(value)
            )

    parsed_decmaker_param: dict[str, object] = {}
    try:
        raw_decmaker_param = json.loads(form_data.get("decmaker_param_json", "{}"))
    except JSONDecodeError:
        raw_decmaker_param = {}
    if isinstance(raw_decmaker_param, dict):
        parsed_decmaker_param = raw_decmaker_param

    decmakers_by_key = {
        str(item["key"]): item for item in engine_chain_decmakers if "key" in item
    }
    default_decmaker = engine_chain_decmakers[0] if engine_chain_decmakers else None
    selected_decmaker = decmakers_by_key.get(
        form_data.get("decmaker_key", ""),
        default_decmaker,
    )
    if selected_decmaker is None:
        form_data["decmaker_key"] = ""
        return

    form_data["decmaker_key"] = str(selected_decmaker["key"])
    default_param = selected_decmaker.get("default_param", {})
    if not isinstance(default_param, dict):
        default_param = {}
    for key, value in default_param.items():
        param_form_key = f"engine_decmaker_param__{key}"
        if param_form_key in form_data:
            continue
        if key in parsed_decmaker_param:
            parsed_value = parsed_decmaker_param[key]
            form_data[param_form_key] = (
                json.dumps(parsed_value)
                if isinstance(parsed_value, bool)
                else str(parsed_value)
            )
            continue
        form_data[param_form_key] = (
            json.dumps(value) if isinstance(value, bool) else str(value)
        )


def _build_engine_chain_payload_from_form_data(
    engine_chain_algorithms: list[dict[str, object]],
    engine_chain_decmakers: list[dict[str, object]],
    form_data: dict[str, str],
) -> dict[str, object]:
    indices = _engine_alertgen_indices(form_data)

    algorithms_by_key = {
        str(item["key"]): item for item in engine_chain_algorithms if "key" in item
    }
    decmakers_by_key = {
        str(item["key"]): item for item in engine_chain_decmakers if "key" in item
    }

    alertgens: list[dict[str, object]] = []
    for position, index in enumerate(indices, start=1):
        alg_key = form_data.get(f"engine_alertgen_{index}_alg_key", "").strip()
        selected_algorithm = algorithms_by_key.get(alg_key)
        if selected_algorithm is None:
            raise ValueError(f"Alertgen {position} requires a runnable algorithm.")
        alg_param: dict[str, object] = {}
        raw_param_schema = selected_algorithm.get("param_schema")
        if not isinstance(raw_param_schema, list):
            raw_param_schema = []
        for item in raw_param_schema:
            if not isinstance(item, dict):
                continue
            param_key = str(item.get("key", "")).strip()
            if not param_key:
                continue
            raw_value = form_data.get(f"engine_alertgen_{index}_param__{param_key}", "")
            if raw_value == "" and item.get("required", False):
                raise ValueError(
                    f"Alertgen {position} {item.get('label') or param_key} is required."
                )
            param_type = str(item.get("type", "string"))
            if param_type == "integer":
                parsed_value: object = int(raw_value)
            elif param_type == "number":
                parsed_value = float(raw_value)
            elif param_type == "boolean":
                parsed_value = raw_value.strip().lower() == "true"
            else:
                parsed_value = raw_value
            alg_param[param_key] = parsed_value
        alertgens.append({"alg_key": alg_key, "alg_param": alg_param})

    decmaker_key = form_data.get("decmaker_key", "").strip()
    selected_decmaker = decmakers_by_key.get(decmaker_key)
    if selected_decmaker is None:
        raise ValueError("A decision maker is required.")
    decmaker_param: dict[str, object] = {}
    raw_decmaker_schema = selected_decmaker.get("param_schema")
    if not isinstance(raw_decmaker_schema, list):
        raw_decmaker_schema = []
    for item in raw_decmaker_schema:
        if not isinstance(item, dict):
            continue
        param_key = str(item.get("key", "")).strip()
        if not param_key:
            continue
        raw_value = form_data.get(f"engine_decmaker_param__{param_key}", "")
        if raw_value == "" and item.get("required", False):
            raise ValueError(
                f"Decision maker {item.get('label') or param_key} is required."
            )
        param_type = str(item.get("type", "string"))
        if param_type == "integer":
            parsed_value = int(raw_value)
        elif param_type == "number":
            parsed_value = float(raw_value)
        elif param_type == "boolean":
            parsed_value = raw_value.strip().lower() == "true"
        else:
            parsed_value = raw_value
        decmaker_param[param_key] = parsed_value

    return {
        "speed_factor": int(form_data.get("speed_factor", "60")),
        "alertgens": alertgens,
        "decmaker": {
            "decmaker_key": decmaker_key,
            "decmaker_param": decmaker_param,
        },
    }


def _set_engine_chain_preview_payload(
    engine_chain_algorithms: list[dict[str, object]],
    engine_chain_decmakers: list[dict[str, object]],
    form_data: dict[str, str],
) -> None:
    try:
        payload = _build_engine_chain_payload_from_form_data(
            engine_chain_algorithms,
            engine_chain_decmakers,
            form_data,
        )
    except (TypeError, ValueError):
        form_data["engine_chain_payload_json"] = ""
        return
    form_data["engine_chain_payload_json"] = json.dumps(payload, indent=2)


def _engine_alertgen_indices(
    form_data: dict[str, str],
    parsed_alertgens: list[dict[str, object]] | None = None,
) -> list[int]:
    raw_order = form_data.get("engine_alertgen_order", "").strip()
    if raw_order:
        try:
            parsed_order = json.loads(raw_order)
        except JSONDecodeError:
            parsed_order = []
        if isinstance(parsed_order, list):
            normalized_order = [
                int(item) for item in parsed_order if isinstance(item, (int, str))
            ]
            normalized_order = [item for item in normalized_order if item > 0]
            if normalized_order:
                return normalized_order

    discovered_indices: set[int] = set()
    pattern = re.compile(r"^engine_alertgen_(\d+)_")
    for key in form_data:
        match = pattern.match(key)
        if match is None:
            continue
        discovered_indices.add(int(match.group(1)))
    if discovered_indices:
        return sorted(discovered_indices)

    if parsed_alertgens:
        return list(range(1, len(parsed_alertgens) + 1))
    return [1]


def _engine_alertgen_rows_for_view(
    engine_chain_algorithms: list[dict[str, object]],
    form_data: dict[str, str],
) -> list[dict[str, object]]:
    algorithms_by_key = {
        str(item["key"]): item for item in engine_chain_algorithms if "key" in item
    }
    rows: list[dict[str, object]] = []
    for index in _engine_alertgen_indices(form_data):
        alg_key = str(form_data.get(f"engine_alertgen_{index}_alg_key", ""))
        selected_algorithm = algorithms_by_key.get(alg_key)
        default_param_value = (
            selected_algorithm.get("default_param", {})
            if isinstance(selected_algorithm, dict)
            else {}
        )
        default_param = (
            dict(default_param_value) if isinstance(default_param_value, dict) else {}
        )
        param_values = {
            key: form_data.get(
                f"engine_alertgen_{index}_param__{key}",
                json.dumps(value) if isinstance(value, bool) else str(value),
            )
            for key, value in default_param.items()
        }
        rows.append(
            {
                "index": index,
                "alg_key": alg_key,
                "param_values": param_values,
            }
        )
    return rows


def _merge_quick_builder_defaults(
    quick_builder_algorithms: list[dict[str, object]],
    form_data: dict[str, str],
) -> None:
    selected_alg_key = form_data.get("quick_builder_alg_key", "")
    selected_algorithm = next(
        (
            algorithm
            for algorithm in quick_builder_algorithms
            if algorithm["key"] == selected_alg_key
        ),
        quick_builder_algorithms[0] if quick_builder_algorithms else None,
    )
    if selected_algorithm is None:
        return

    form_data["quick_builder_alg_key"] = str(selected_algorithm["key"])
    default_param = selected_algorithm.get("default_param", {})
    if not isinstance(default_param, dict):
        return
    for key, value in default_param.items():
        form_key = f"quick_param__{key}"
        if form_key not in form_data:
            form_data[form_key] = (
                json.dumps(value) if isinstance(value, bool) else str(value)
            )


def _build_quick_builder_configuration_payload(
    quick_builder_algorithms: list[dict[str, object]],
    form_data: dict[str, str],
) -> dict[str, object]:
    alg_key = form_data.get("quick_builder_alg_key", "").strip()
    selected_algorithm = next(
        (
            algorithm
            for algorithm in quick_builder_algorithms
            if algorithm["key"] == alg_key
        ),
        None,
    )
    if selected_algorithm is None:
        raise ValueError("A supported quick-builder algorithm is required.")

    alg_param: dict[str, object] = {}
    raw_param_schema = selected_algorithm.get("param_schema")
    if not isinstance(raw_param_schema, list):
        raw_param_schema = []
    for item in raw_param_schema:
        if not isinstance(item, dict):
            continue
        param_key = str(item.get("key", "")).strip()
        if not param_key:
            continue
        raw_value = form_data.get(f"quick_param__{param_key}", "")
        if raw_value == "" and item.get("required", False):
            raise ValueError(f"{item.get('label') or param_key} is required.")

        param_type = str(item.get("type", "string"))
        if param_type == "integer":
            parsed_value: object = int(raw_value)
        elif param_type == "number":
            parsed_value = float(raw_value)
        elif param_type == "boolean":
            parsed_value = raw_value.strip().lower() == "true"
        else:
            parsed_value = raw_value

        alg_param[param_key] = parsed_value

    configuration_payload = build_single_algorithm_configuration_payload(
        alg_key=alg_key,
        alg_param=alg_param,
    )
    nodes = configuration_payload.get("nodes")
    if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict):
        nodes[0]["buy_enabled"] = (
            form_data.get("quick_builder_buy_enabled", "true").strip().lower() == "true"
        )
        nodes[0]["sell_enabled"] = (
            form_data.get("quick_builder_sell_enabled", "true").strip().lower()
            == "true"
        )
    return configuration_payload


def _quick_builder_form_data_from_payload(
    configuration_payload: dict[str, object],
) -> dict[str, str]:
    extracted = extract_single_algorithm_from_configuration_payload(
        configuration_payload
    )
    if extracted is None:
        return {}

    form_data = {
        "configuration_source": "quick_builder",
        "quick_builder_alg_key": str(extracted["alg_key"]),
        "quick_builder_buy_enabled": "true" if extracted["buy"] else "false",
        "quick_builder_sell_enabled": "true" if extracted["sell"] else "false",
    }
    alg_param = extracted.get("alg_param", {})
    if isinstance(alg_param, dict):
        for key, value in alg_param.items():
            form_data[f"quick_param__{key}"] = (
                json.dumps(value) if isinstance(value, bool) else str(value)
            )
    return form_data


def _serialize_recent_experiment(experiment: dict[str, object]) -> dict[str, str]:
    time_range = experiment.get("time_range")
    if not isinstance(time_range, dict):
        time_range = {}

    selected_algorithms = experiment.get("selected_algorithms")
    if not isinstance(selected_algorithms, list):
        selected_algorithms = []

    created_at = experiment.get("created_at")
    created_at_label = ""
    if isinstance(created_at, datetime):
        created_at_label = created_at.strftime("%Y-%m-%d %H:%M UTC")

    serialized_algorithms = [
        {
            "alg_key": algorithm.get("alg_key"),
            "alg_param": algorithm.get("alg_param", {}),
        }
        for algorithm in selected_algorithms
        if isinstance(algorithm, dict) and isinstance(algorithm.get("alg_key"), str)
    ]

    return {
        "experiment_id": str(experiment.get("experiment_id", "")),
        "symbol": str(experiment.get("symbol", "")),
        "start_date": str(time_range.get("start", ""))[:10],
        "start_time": str(time_range.get("start", ""))[11:16],
        "end_date": str(time_range.get("end", ""))[:10],
        "end_time": str(time_range.get("end", ""))[11:16],
        "notes": str(experiment.get("notes", "")),
        "configuration_json": json.dumps(
            experiment.get("input_snapshot")
            if experiment.get("input_kind") == "configuration"
            and isinstance(experiment.get("input_snapshot"), dict)
            else build_single_algorithm_configuration_payload(
                alg_key=str(serialized_algorithms[0]["alg_key"]),
                alg_param=_as_str_any_dict(
                    serialized_algorithms[0].get("alg_param", {})
                ),
            )
            if serialized_algorithms
            else {}
        ),
        "algorithm_count": str(len(serialized_algorithms)),
        "created_at_label": created_at_label,
    }


def _recent_experiment_signature(experiment: dict[str, object]) -> str | None:
    time_range = experiment.get("time_range")
    if not isinstance(time_range, dict):
        time_range = {}

    signature_payload: dict[str, object] = {
        "symbol": str(experiment.get("symbol", "")),
        "start": str(time_range.get("start", "")),
        "end": str(time_range.get("end", "")),
        "notes": str(experiment.get("notes", "")),
    }

    selected_algorithms = experiment.get("selected_algorithms")
    if isinstance(selected_algorithms, list) and len(selected_algorithms) > 0:
        normalized_algorithms = [
            {
                "alg_key": algorithm.get("alg_key"),
                "alg_param": algorithm.get("alg_param", {}),
            }
            for algorithm in selected_algorithms
            if isinstance(algorithm, dict) and isinstance(algorithm.get("alg_key"), str)
        ]
        if normalized_algorithms:
            signature_payload["input_kind"] = "single_algorithm"
            signature_payload["algorithms"] = normalized_algorithms
            return json.dumps(
                signature_payload,
                sort_keys=True,
            )

    input_kind = experiment.get("input_kind")
    input_snapshot = experiment.get("input_snapshot")

    if input_kind == "configuration" and isinstance(input_snapshot, dict):
        signature_payload["input_kind"] = "configuration"
        signature_payload["configuration"] = input_snapshot
        return json.dumps(
            signature_payload,
            sort_keys=True,
        )

    if input_kind == "single_algorithm" and isinstance(input_snapshot, dict):
        algorithms = input_snapshot.get("algorithms")
        if isinstance(algorithms, list) and len(algorithms) > 0:
            normalized_algorithms = [
                {
                    "alg_key": algorithm.get("alg_key"),
                    "alg_param": algorithm.get("alg_param", {}),
                }
                for algorithm in algorithms
                if isinstance(algorithm, dict)
                and isinstance(algorithm.get("alg_key"), str)
            ]
            if normalized_algorithms:
                signature_payload["input_kind"] = "single_algorithm"
                signature_payload["algorithms"] = normalized_algorithms
                return json.dumps(
                    signature_payload,
                    sort_keys=True,
                )

    return None


def _decorate_experiment(experiment: dict[str, object]) -> dict[str, object]:
    decorated = dict(experiment)
    queue_enqueued_at = decorated.get("queue_enqueued_at")
    if isinstance(queue_enqueued_at, datetime) and queue_enqueued_at.tzinfo is None:
        queue_enqueued_at = queue_enqueued_at.replace(tzinfo=timezone.utc)
        decorated["queue_enqueued_at"] = queue_enqueued_at
    started_at = decorated.get("started_at")
    if isinstance(started_at, datetime) and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
        decorated["started_at"] = started_at
    decorated["queue_enqueued_at_epoch_ms"] = (
        int(queue_enqueued_at.timestamp() * 1000)
        if isinstance(queue_enqueued_at, datetime)
        else None
    )
    decorated["started_at_epoch_ms"] = (
        int(started_at.timestamp() * 1000) if isinstance(started_at, datetime) else None
    )
    decorated["is_queued"] = decorated.get("status") == "queued"
    decorated["is_running"] = decorated.get("status") == "running"
    decorated["is_cancelling"] = decorated.get("status") == "cancelling"
    decorated["is_failed"] = decorated.get("status") == "failed"
    decorated["is_cancelled"] = decorated.get("status") == "cancelled"
    return decorated


def _serialize_experiment_runtime(experiment: dict[str, object]) -> dict[str, object]:
    serialized = dict(experiment)
    for field in (
        "created_at",
        "updated_at",
        "queue_enqueued_at",
        "started_at",
        "finished_at",
    ):
        value = serialized.get(field)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            serialized[field] = value.astimezone(timezone.utc).isoformat()
    return serialized


def _recent_experiment_presets() -> list[dict[str, str]]:
    repo = current_app.extensions["experiment_repository"]
    experiments = repo.list_experiments()
    recent_distinct_experiments: list[dict[str, object]] = []
    seen_signatures: set[str] = set()

    for experiment in experiments:
        signature = _recent_experiment_signature(experiment)
        if signature is None or signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        recent_distinct_experiments.append(experiment)
        if len(recent_distinct_experiments) == 3:
            break

    return [
        _serialize_recent_experiment(experiment)
        for experiment in recent_distinct_experiments
    ]


def _load_configuration_preset(draft_id: str | None) -> dict[str, str] | None:
    if not draft_id:
        return None
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        return None
    draft = payload["draft"]
    configuration_payload = draft.get("payload")
    if not isinstance(configuration_payload, dict):
        return None
    return {
        "draft_id": str(draft.get("draft_id", "")),
        "config_key": str(draft.get("config_key", "")),
        "name": str(draft.get("name", "")),
        "version": str(configuration_payload.get("version", "")),
        "configuration_json": json.dumps(configuration_payload),
    }


def _list_configuration_presets() -> list[dict[str, str]]:
    drafts = current_app.extensions["configuration_builder_service"].list_drafts()
    presets: list[dict[str, str]] = []
    for draft in drafts:
        if not isinstance(draft, dict):
            continue
        payload = draft.get("payload")
        payload_dict = payload if isinstance(payload, dict) else {}
        updated_at = draft.get("updated_at")
        updated_at_label = ""
        updated_at_sort_key = ""
        if isinstance(updated_at, datetime):
            updated_at_label = updated_at.strftime("%Y-%m-%d %H:%M UTC")
            updated_at_sort_key = updated_at.isoformat()
        structure_lines = _build_configuration_structure_lines(payload_dict)
        preflight = _build_configuration_preflight(payload_dict)
        nodes = payload_dict.get("nodes")
        node_count = len(nodes) if isinstance(nodes, list) else 0
        algorithm_count = 0
        group_count = 0
        if isinstance(nodes, list):
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node_type = str(node.get("node_type", ""))
                if node_type == "algorithm":
                    algorithm_count += 1
                elif node_type in {"and", "or", "pipeline"}:
                    group_count += 1
        presets.append(
            {
                "draft_id": str(draft.get("draft_id", "")),
                "config_key": str(draft.get("config_key", "")),
                "name": str(draft.get("name", "")) or "Unnamed configuration",
                "version": str(payload_dict.get("version", "")),
                "status": str(draft.get("status", "draft")),
                "root_node_id": str(payload_dict.get("root_node_id", "")),
                "node_count": str(node_count),
                "algorithm_count": str(algorithm_count),
                "group_count": str(group_count),
                "configuration_json": json.dumps(payload_dict, indent=2),
                "structure_lines": "\n".join(structure_lines),
                "preflight_valid": "true" if preflight["is_valid"] else "false",
                "preflight_errors": "\n".join(_preflight_messages(preflight, "errors")),
                "preflight_warnings": "\n".join(
                    _preflight_messages(preflight, "warnings")
                ),
                "updated_at_label": updated_at_label,
                "updated_at_sort_key": updated_at_sort_key,
            }
        )
    return sorted(presets, key=lambda item: (item["name"], item["draft_id"]))


def _recent_configuration_presets(
    presets: list[dict[str, str]],
) -> list[dict[str, str]]:
    sorted_presets = sorted(
        presets,
        key=lambda item: (item["updated_at_sort_key"], item["draft_id"]),
        reverse=True,
    )
    return sorted_presets[:3]


def _build_configuration_structure_lines(payload: dict[str, object]) -> list[str]:
    nodes = payload.get("nodes") or []
    if not isinstance(nodes, list):
        return []
    nodes_by_id = {
        str(node.get("node_id")): node for node in nodes if isinstance(node, dict)
    }

    def render(node_id: str, depth: int) -> list[str]:
        node = nodes_by_id.get(node_id)
        if node is None:
            return []
        prefix = "  " * depth + "- "
        node_type = str(node.get("node_type", "unknown"))
        if node_type == "algorithm":
            alg_key = str(node.get("alg_key", ""))
            node_name = str(node.get("name") or alg_key or node_id)
            return [f"{prefix}{node_name} ({alg_key})"]
        node_name = str(node.get("name") or node_type.upper())
        children = node.get("children") or []
        lines = [f"{prefix}{node_name} [{node_type.upper()}]"]
        if isinstance(children, list):
            for child_id in children:
                lines.extend(render(str(child_id), depth + 1))
        return lines

    root_node_id = payload.get("root_node_id")
    if not isinstance(root_node_id, str) or not root_node_id:
        return []
    return render(root_node_id, 0)


def _build_configuration_preflight(payload: dict[str, object]) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        normalized = validate_configuration_payload(payload)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
        }

    if len(normalized.nodes) >= 10:
        warnings.append(
            "Large configuration; review structure carefully before queueing."
        )

    return {
        "is_valid": True,
        "errors": errors,
        "warnings": warnings,
    }


def _preflight_messages(
    preflight: dict[str, object],
    key: str,
) -> list[str]:
    value = preflight.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _load_algorithm_preset(alg_key: str | None) -> dict[str, str] | None:
    if not alg_key:
        return None
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]
    try:
        algorithm_spec = algorithm_catalog_service.get_algorithm_implementation(alg_key)
    except ValueError:
        return None
    return {
        "configuration_json": json.dumps(
            build_single_algorithm_configuration_payload(
                alg_key=str(algorithm_spec["key"]),
                alg_param=_as_str_any_dict(algorithm_spec.get("default_param", {})),
            )
        )
    }


def _render_new_experiment(
    *,
    status_code: int = 200,
    form_data: dict[str, str] | None = None,
) -> Response:
    catalog = current_app.extensions[
        "algorithm_catalog_service"
    ].list_algorithm_implementations()
    quick_builder_algorithms = _build_quick_builder_algorithms(catalog)
    engine_chain_algorithms = _build_engine_chain_algorithms(catalog)
    configuration_presets = _list_configuration_presets()
    pinned_configuration_presets, unpinned_configuration_presets = (
        _decorate_configuration_presets(configuration_presets)
    )
    recent_configuration_presets = _recent_configuration_presets(
        unpinned_configuration_presets
    )
    configuration_presets = unpinned_configuration_presets
    pinned_quick_builder_presets, recent_quick_builder_presets = (
        _quick_builder_presets_for_view()
    )
    decmakers = current_app.extensions[
        "algorithm_catalog_service"
    ].list_decmaker_implementations()
    engine_chain_decmakers = _build_engine_chain_decmakers(decmakers)
    runtime_settings = current_app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()

    effective_form_data = _experiment_form_defaults(catalog)
    effective_form_data.update(
        load_form_state(request.cookies.get(_EXPERIMENT_FORM_COOKIE))
    )
    selected_configuration = _load_configuration_preset(request.args.get("draft_id"))
    selected_algorithm = _load_algorithm_preset(request.args.get("alg_key"))
    if selected_configuration is not None:
        effective_form_data["run_mode"] = "configuration"
        effective_form_data["configuration_source"] = "saved_configuration"
        effective_form_data["selected_draft_id"] = selected_configuration["draft_id"]
        effective_form_data["configuration_json"] = selected_configuration[
            "configuration_json"
        ]
    elif selected_algorithm is not None:
        effective_form_data["run_mode"] = "configuration"
        effective_form_data["configuration_source"] = "quick_builder"
        effective_form_data["configuration_json"] = selected_algorithm[
            "configuration_json"
        ]
        try:
            selected_algorithm_payload = json.loads(
                selected_algorithm["configuration_json"]
            )
        except JSONDecodeError:
            pass
        else:
            if isinstance(selected_algorithm_payload, dict):
                effective_form_data.update(
                    _quick_builder_form_data_from_payload(selected_algorithm_payload)
                )
    if form_data is not None:
        effective_form_data.update(form_data)

    if (
        effective_form_data.get("configuration_source") == "saved_configuration"
        and not selected_configuration
    ):
        selected_configuration = _load_configuration_preset(
            effective_form_data.get("selected_draft_id")
        )
        if selected_configuration is not None:
            effective_form_data["configuration_json"] = selected_configuration[
                "configuration_json"
            ]

    _merge_quick_builder_defaults(quick_builder_algorithms, effective_form_data)
    _merge_engine_chain_defaults(
        engine_chain_algorithms,
        engine_chain_decmakers,
        effective_form_data,
    )
    _set_engine_chain_preview_payload(
        engine_chain_algorithms,
        engine_chain_decmakers,
        effective_form_data,
    )

    if (
        selected_configuration is None
        and effective_form_data["configuration_json"].strip()
    ):
        try:
            configuration_payload = json.loads(
                effective_form_data["configuration_json"]
            )
        except JSONDecodeError:
            selected_configuration = None
        else:
            if isinstance(configuration_payload, dict):
                selected_configuration = {
                    "draft_id": "",
                    "config_key": str(configuration_payload.get("config_key", "")),
                    "name": str(configuration_payload.get("name", "")),
                    "version": str(configuration_payload.get("version", "")),
                    "configuration_json": effective_form_data["configuration_json"],
                }
                if (
                    effective_form_data.get("configuration_source")
                    != "configuration_json"
                ):
                    effective_form_data.update(
                        _quick_builder_form_data_from_payload(configuration_payload)
                    )

    return Response(
        render_template(
            "experiments/new.html",
            algorithms=catalog,
            quick_builder_algorithms=quick_builder_algorithms,
            engine_chain_algorithms=engine_chain_algorithms,
            engine_alertgen_rows=_engine_alertgen_rows_for_view(
                engine_chain_algorithms,
                effective_form_data,
            ),
            configuration_presets=configuration_presets,
            pinned_configuration_presets=pinned_configuration_presets,
            recent_configuration_presets=recent_configuration_presets,
            pinned_quick_builder_presets=pinned_quick_builder_presets,
            recent_quick_builder_presets=recent_quick_builder_presets,
            decmakers=decmakers,
            engine_chain_decmakers=engine_chain_decmakers,
            recent_experiments=_recent_experiment_presets(),
            selected_configuration=selected_configuration,
            form_data=effective_form_data,
            max_concurrent_experiments=runtime_settings["max_concurrent_experiments"],
        ),
        status=status_code,
    )


def _bulk_experiment_form_defaults() -> dict[str, str]:
    return {
        "bulk_mode": "all_algorithms_for_symbol",
        "symbol": "",
        "symbols_text": "",
        "alg_key": "",
        "skip_non_executable_defaults": "true",
        "start_date": "",
        "start_time": "09:30",
        "end_date": "",
        "end_time": "16:00",
        "notes": "",
    }


def _render_bulk_experiment(
    *,
    status_code: int = 200,
    form_data: dict[str, str] | None = None,
) -> Response:
    runtime_settings = current_app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]
    effective_form_data = _bulk_experiment_form_defaults()
    effective_form_data.update(
        load_form_state(request.cookies.get(_BULK_EXPERIMENT_FORM_COOKIE))
    )
    if form_data is not None:
        effective_form_data.update(form_data)
    return Response(
        render_template(
            "experiments/bulk.html",
            form_data=effective_form_data,
            runnable_algorithms=(
                algorithm_catalog_service.list_runnable_algorithm_implementations()
            ),
            max_concurrent_experiments=runtime_settings["max_concurrent_experiments"],
        ),
        status=status_code,
    )


def _collect_submitted_experiment_form_data() -> dict[str, str]:
    configuration_source = request.form.get("configuration_source", "").strip()
    if not configuration_source:
        configuration_source = (
            "quick_builder"
            if request.form.get("quick_builder_alg_key", "").strip()
            else "configuration_json"
        )

    submitted_form_data = {
        "run_mode": request.form.get("run_mode", "configuration"),
        "configuration_source": configuration_source,
        "selected_draft_id": request.form.get("selected_draft_id", ""),
        "quick_builder_alg_key": request.form.get("quick_builder_alg_key", ""),
        "quick_builder_buy_enabled": request.form.get(
            "quick_builder_buy_enabled", "true"
        ),
        "quick_builder_sell_enabled": request.form.get(
            "quick_builder_sell_enabled", "true"
        ),
        "symbol": request.form.get("symbol", ""),
        "start_date": request.form.get("start_date", ""),
        "start_time": request.form.get("start_time", ""),
        "end_date": request.form.get("end_date", ""),
        "end_time": request.form.get("end_time", ""),
        "alertgens_json": request.form.get("alertgens_json", "[]"),
        "decmaker_key": request.form.get("decmaker_key", "alg1"),
        "decmaker_param_json": request.form.get("decmaker_param_json", "{}"),
        "speed_factor": request.form.get("speed_factor", "60"),
        "notes": request.form.get("notes", ""),
        "configuration_json": request.form.get("configuration_json", ""),
        "max_concurrent_experiments": str(
            current_app.config.get("EXPERIMENT_MAX_CONCURRENT_RUNS", 1)
        ),
    }
    for key, value in request.form.items():
        if key.startswith("quick_param__"):
            submitted_form_data[key] = value
        if key.startswith("engine_alertgen_") or key.startswith(
            "engine_decmaker_param__"
        ):
            submitted_form_data[key] = value
    return submitted_form_data


def _experiment_form_preferences() -> dict[str, object]:
    repository = current_app.extensions["experiment_form_preferences_repository"]
    stored = repository.get_preferences() or {}
    pinned_configuration_draft_ids = stored.get("pinned_configuration_draft_ids")
    recent_quick_builder_presets = stored.get("recent_quick_builder_presets")
    pinned_quick_builder_presets = stored.get("pinned_quick_builder_presets")
    pinned_configuration_ids_list = (
        pinned_configuration_draft_ids
        if isinstance(pinned_configuration_draft_ids, list)
        else []
    )
    recent_quick_presets_list = (
        recent_quick_builder_presets
        if isinstance(recent_quick_builder_presets, list)
        else []
    )
    pinned_quick_presets_list = (
        pinned_quick_builder_presets
        if isinstance(pinned_quick_builder_presets, list)
        else []
    )
    return {
        "pinned_configuration_draft_ids": [
            str(item) for item in pinned_configuration_ids_list
        ],
        "recent_quick_builder_presets": [
            dict(item) for item in recent_quick_presets_list if isinstance(item, dict)
        ],
        "pinned_quick_builder_presets": [
            dict(item) for item in pinned_quick_presets_list if isinstance(item, dict)
        ],
    }


def _save_experiment_form_preferences(preferences: dict[str, object]) -> None:
    current_app.extensions["experiment_form_preferences_repository"].save_preferences(
        preferences
    )


def _quick_builder_preset_from_form_data(form_data: dict[str, str]) -> dict[str, str]:
    preset = {
        "alg_key": form_data.get("quick_builder_alg_key", ""),
        "buy_enabled": form_data.get("quick_builder_buy_enabled", "true"),
        "sell_enabled": form_data.get("quick_builder_sell_enabled", "true"),
    }
    for key, value in form_data.items():
        if key.startswith("quick_param__"):
            preset[key] = value
    return preset


def _quick_builder_preset_signature(preset: dict[str, str]) -> str:
    return json.dumps(preset, sort_keys=True)


def _record_recent_quick_builder_preset(form_data: dict[str, str]) -> None:
    preferences = _experiment_form_preferences()
    preset = _quick_builder_preset_from_form_data(form_data)
    signature = _quick_builder_preset_signature(preset)
    recent_presets = preferences["recent_quick_builder_presets"]
    if not isinstance(recent_presets, list):
        recent_presets = []
    recents = [
        item
        for item in recent_presets
        if isinstance(item, dict)
        and _quick_builder_preset_signature(
            {str(key): str(value) for key, value in item.items()}
        )
        != signature
    ]
    updated_recents = [preset, *recents][:5]
    preferences["recent_quick_builder_presets"] = updated_recents
    _save_experiment_form_preferences(preferences)


def _toggle_pinned_configuration(draft_id: str) -> None:
    preferences = _experiment_form_preferences()
    pinned_configuration_ids = preferences["pinned_configuration_draft_ids"]
    if not isinstance(pinned_configuration_ids, list):
        pinned_configuration_ids = []
    pinned_ids = [
        str(item) for item in pinned_configuration_ids if str(item) != draft_id
    ]
    if draft_id not in pinned_configuration_ids:
        pinned_ids.insert(0, draft_id)
    preferences["pinned_configuration_draft_ids"] = pinned_ids
    _save_experiment_form_preferences(preferences)


def _toggle_pinned_quick_builder_preset(form_data: dict[str, str]) -> None:
    preferences = _experiment_form_preferences()
    preset = _quick_builder_preset_from_form_data(form_data)
    signature = _quick_builder_preset_signature(preset)
    pinned_presets = preferences["pinned_quick_builder_presets"]
    if not isinstance(pinned_presets, list):
        pinned_presets = []
    pinned = [
        item
        for item in pinned_presets
        if isinstance(item, dict)
        and _quick_builder_preset_signature(
            {str(key): str(value) for key, value in item.items()}
        )
        != signature
    ]
    if len(pinned) == len(pinned_presets):
        pinned.insert(0, preset)
    preferences["pinned_quick_builder_presets"] = pinned[:5]
    _save_experiment_form_preferences(preferences)


def _decorate_configuration_presets(
    presets: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    preferences = _experiment_form_preferences()
    raw_pinned_id_list = preferences.get("pinned_configuration_draft_ids", [])
    pinned_id_list = (
        [str(item) for item in raw_pinned_id_list]
        if isinstance(raw_pinned_id_list, list)
        else []
    )
    pinned_ids = set(pinned_id_list)
    pinned: list[dict[str, str]] = []
    unpinned: list[dict[str, str]] = []
    for preset in presets:
        decorated = {
            **preset,
            "is_pinned": "true" if preset["draft_id"] in pinned_ids else "false",
        }
        if preset["draft_id"] in pinned_ids:
            pinned.append(decorated)
        else:
            unpinned.append(decorated)
    pinned.sort(
        key=lambda item: (
            pinned_id_list.index(item["draft_id"])
            if item["draft_id"] in pinned_id_list
            else 999
        )
    )
    return pinned, unpinned


def _quick_builder_presets_for_view() -> tuple[
    list[dict[str, str]], list[dict[str, str]]
]:
    preferences = _experiment_form_preferences()
    raw_pinned_source = preferences.get("pinned_quick_builder_presets", [])
    raw_recent_source = preferences.get("recent_quick_builder_presets", [])
    pinned_source = (
        [dict(item) for item in raw_pinned_source if isinstance(item, dict)]
        if isinstance(raw_pinned_source, list)
        else []
    )
    recent_source = (
        [dict(item) for item in raw_recent_source if isinstance(item, dict)]
        if isinstance(raw_recent_source, list)
        else []
    )
    pinned = [
        {**item, "label": item.get("alg_key", "Quick preset")} for item in pinned_source
    ]
    pinned_signatures = {
        _quick_builder_preset_signature(
            {str(key): str(value) for key, value in item.items()}
        )
        for item in pinned_source
    }
    recent = [
        {**item, "label": item.get("alg_key", "Quick preset")}
        for item in recent_source
        if _quick_builder_preset_signature(
            {str(key): str(value) for key, value in item.items()}
        )
        not in pinned_signatures
    ]
    return pinned, recent


def _quick_builder_configuration_payload_from_request() -> dict[str, object]:
    submitted_form_data = _collect_submitted_experiment_form_data()
    quick_builder_algorithms = _build_quick_builder_algorithms(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_algorithm_implementations()
    )
    return _build_quick_builder_configuration_payload(
        quick_builder_algorithms,
        submitted_form_data,
    )


def _configuration_template_payload(template_key: str) -> dict[str, object]:
    if template_key == "single_algorithm":
        return build_single_algorithm_configuration_payload(
            alg_key="OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            alg_param={"window": 2},
        )

    if template_key == "and_strategy":
        return {
            "config_key": "template-and-strategy",
            "version": "1",
            "name": "Template AND strategy",
            "root_node_id": "group1",
            "nodes": [
                {
                    "node_id": "group1",
                    "node_type": "and",
                    "name": "AND group",
                    "children": ["alg1", "alg2"],
                },
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                },
                {
                    "node_id": "alg2",
                    "node_type": "algorithm",
                    "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                    "alg_param": {"period": 5},
                    "buy_enabled": True,
                    "sell_enabled": True,
                },
            ],
            "runtime_overrides": {},
            "compatibility_metadata": {},
        }

    if template_key == "or_strategy":
        return {
            "config_key": "template-or-strategy",
            "version": "1",
            "name": "Template OR strategy",
            "root_node_id": "group1",
            "nodes": [
                {
                    "node_id": "group1",
                    "node_type": "or",
                    "name": "OR group",
                    "children": ["alg1", "alg2"],
                },
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                },
                {
                    "node_id": "alg2",
                    "node_type": "algorithm",
                    "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                    "alg_param": {"period": 5},
                    "buy_enabled": True,
                    "sell_enabled": True,
                },
            ],
            "runtime_overrides": {},
            "compatibility_metadata": {},
        }

    if template_key == "breakout_example":
        return {
            "config_key": "template-breakout-example",
            "version": "1",
            "name": "Template breakout example",
            "root_node_id": "group1",
            "nodes": [
                {
                    "node_id": "group1",
                    "node_type": "and",
                    "name": "Breakout confirmation",
                    "children": ["alg1", "alg2"],
                },
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                },
                {
                    "node_id": "alg2",
                    "node_type": "algorithm",
                    "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                    "alg_param": {"period": 5},
                    "buy_enabled": True,
                    "sell_enabled": False,
                },
            ],
            "runtime_overrides": {},
            "compatibility_metadata": {},
        }

    raise ValueError(f"Unsupported configuration template: {template_key}")


@bp.get("")
def history():
    service = current_app.extensions["experiment_service"]
    repo = current_app.extensions["experiment_repository"]
    experiments = [_decorate_experiment(item) for item in repo.list_experiments()]
    queue_overview = service.get_queue_overview()
    running_experiments = queue_overview.get("running_experiments") or []
    queued_experiments = queue_overview.get("queued_experiments") or []
    history_experiments = [
        experiment
        for experiment in experiments
        if experiment.get("status") not in {"queued", "running"}
    ]
    return render_template(
        "experiments/history.html",
        experiments=history_experiments,
        running_experiments=[
            _decorate_experiment(item)
            for item in running_experiments
            if isinstance(item, dict)
        ],
        queued_experiments=[
            _decorate_experiment(item)
            for item in queued_experiments
            if isinstance(item, dict)
        ],
        queue_summary=queue_overview.get("queue_summary") or {},
    )


@bp.get("/new")
def new_experiment():
    return _render_new_experiment()


@bp.get("/bulk")
def bulk_experiment():
    return _render_bulk_experiment()


@bp.post("/quick-builder/save-draft")
def save_quick_builder_as_draft():
    submitted_form_data = _collect_submitted_experiment_form_data()
    try:
        configuration_payload = _quick_builder_configuration_payload_from_request()
        draft_id = current_app.extensions["configuration_builder_service"].create_draft(
            configuration_payload
        )
        _record_recent_quick_builder_preset(submitted_form_data)
    except ValueError as exc:
        flash(str(exc), "danger")
        return _render_new_experiment(
            status_code=400,
            form_data=submitted_form_data,
        )
    flash("Quick-builder configuration saved as draft.", "success")
    return redirect(url_for("configurations.detail_configuration", draft_id=draft_id))


@bp.post("/quick-builder/open-in-builder")
def open_quick_builder_in_builder():
    submitted_form_data = _collect_submitted_experiment_form_data()
    try:
        configuration_payload = _quick_builder_configuration_payload_from_request()
        draft_id = current_app.extensions["configuration_builder_service"].create_draft(
            configuration_payload
        )
        _record_recent_quick_builder_preset(submitted_form_data)
    except ValueError as exc:
        flash(str(exc), "danger")
        return _render_new_experiment(
            status_code=400,
            form_data=submitted_form_data,
        )
    flash("Quick-builder configuration opened in the full builder.", "success")
    return redirect(url_for("configurations.edit_configuration", draft_id=draft_id))


@bp.post("/configuration-templates/<template_key>/open-in-builder")
def open_configuration_template_in_builder(template_key: str):
    try:
        draft_id = current_app.extensions["configuration_builder_service"].create_draft(
            _configuration_template_payload(template_key)
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return _render_new_experiment(status_code=400)
    flash("Configuration template opened in the full builder.", "success")
    return redirect(url_for("configurations.edit_configuration", draft_id=draft_id))


@bp.post("/saved-configurations/<draft_id>/toggle-pin")
def toggle_pinned_saved_configuration(draft_id: str):
    _toggle_pinned_configuration(draft_id)
    return redirect(url_for("experiments.new_experiment", draft_id=draft_id))


@bp.post("/quick-builder/toggle-pin")
def toggle_pinned_quick_builder():
    submitted_form_data = _collect_submitted_experiment_form_data()
    _toggle_pinned_quick_builder_preset(submitted_form_data)
    return _render_new_experiment(form_data=submitted_form_data)


@bp.post("/<experiment_id>/cancel")
def cancel_experiment(experiment_id: str):
    service = current_app.extensions["experiment_service"]
    try:
        was_requested = service.request_cancel(experiment_id)
    except ValueError:
        abort(404)

    if was_requested:
        flash("Experiment removed from execution queue.", "info")
        experiment = service.get_experiment_detail(experiment_id)
        if (
            experiment is not None
            and experiment["experiment"].get("status") == "cancelled"
        ):
            return redirect(url_for("experiments.detail", experiment_id=experiment_id))
    else:
        flash(
            "Experiment is no longer queued or running and cannot be cancelled.",
            "warning",
        )

    return redirect(url_for("experiments.detail", experiment_id=experiment_id))


@bp.post("/<experiment_id>/delete")
def delete_experiment(experiment_id: str):
    deleted = current_app.extensions["experiment_service"].delete_experiment(
        experiment_id
    )
    if not deleted:
        flash("Running experiments cannot be deleted.", "warning")
        return redirect(url_for("experiments.detail", experiment_id=experiment_id))
    flash(f"Experiment deleted; experiment_id={experiment_id}", "success")
    return redirect(url_for("experiments.history"))


@bp.post("")
def create_experiment():
    submitted_form_data = _collect_submitted_experiment_form_data()

    service = current_app.extensions["experiment_service"]
    quick_builder_algorithms = _build_quick_builder_algorithms(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_algorithm_implementations()
    )
    engine_chain_algorithms = _build_engine_chain_algorithms(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_algorithm_implementations()
    )
    engine_chain_decmakers = _build_engine_chain_decmakers(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_decmaker_implementations()
    )
    try:
        configuration_payload = None
        engine_chain_payload = None
        if submitted_form_data["run_mode"] == "configuration":
            if submitted_form_data["configuration_source"] == "quick_builder":
                configuration_payload = _build_quick_builder_configuration_payload(
                    quick_builder_algorithms,
                    submitted_form_data,
                )
                _record_recent_quick_builder_preset(submitted_form_data)
            elif submitted_form_data["configuration_source"] == "saved_configuration":
                selected_configuration = _load_configuration_preset(
                    submitted_form_data["selected_draft_id"]
                )
                if selected_configuration is None:
                    raise ValueError("A saved configuration must be selected.")
                configuration_payload = json.loads(
                    selected_configuration["configuration_json"]
                )
            else:
                configuration_payload = json.loads(
                    submitted_form_data["configuration_json"]
                )
        elif submitted_form_data["run_mode"] == "engine_chain":
            has_engine_chain_gui_fields = any(
                key.startswith("engine_alertgen_")
                or key.startswith("engine_decmaker_param__")
                for key in submitted_form_data
            )
            if has_engine_chain_gui_fields:
                engine_chain_payload = _build_engine_chain_payload_from_form_data(
                    engine_chain_algorithms,
                    engine_chain_decmakers,
                    submitted_form_data,
                )
            else:
                engine_chain_payload = {
                    "speed_factor": int(submitted_form_data["speed_factor"]),
                    "alertgens": json.loads(submitted_form_data["alertgens_json"]),
                    "decmaker": {
                        "decmaker_key": submitted_form_data["decmaker_key"],
                        "decmaker_param": json.loads(
                            submitted_form_data["decmaker_param_json"]
                        ),
                    },
                }
            decmaker_payload = engine_chain_payload.get("decmaker")
            decmaker_param_payload = (
                decmaker_payload.get("decmaker_param")
                if isinstance(decmaker_payload, dict)
                else {}
            )
            submitted_form_data["alertgens_json"] = json.dumps(
                engine_chain_payload["alertgens"],
                indent=2,
            )
            submitted_form_data["decmaker_param_json"] = json.dumps(
                decmaker_param_payload,
                indent=2,
            )
            submitted_form_data["engine_chain_payload_json"] = json.dumps(
                engine_chain_payload,
                indent=2,
            )
        experiment_id = service.create_experiment(
            symbol=submitted_form_data["symbol"],
            start_date=submitted_form_data["start_date"],
            start_time=submitted_form_data["start_time"],
            end_date=submitted_form_data["end_date"],
            end_time=submitted_form_data["end_time"],
            algorithms=[],
            configuration_payload=configuration_payload,
            engine_chain_payload=engine_chain_payload,
            notes=submitted_form_data["notes"],
        )
    except JSONDecodeError:
        flash("Configuration JSON must be valid JSON.", "danger")
        response = _render_new_experiment(
            status_code=400, form_data=submitted_form_data
        )
        persist_form_state(
            response,
            cookie_name=_EXPERIMENT_FORM_COOKIE,
            form_data=submitted_form_data,
        )
        return response
    except MarketDataUnavailableError as exc:
        flash(str(exc), "danger")
        response = _render_new_experiment(
            status_code=400, form_data=submitted_form_data
        )
        persist_form_state(
            response,
            cookie_name=_EXPERIMENT_FORM_COOKIE,
            form_data=submitted_form_data,
        )
        return response
    except ValueError as exc:
        flash(str(exc), "danger")
        response = _render_new_experiment(
            status_code=400, form_data=submitted_form_data
        )
        persist_form_state(
            response,
            cookie_name=_EXPERIMENT_FORM_COOKIE,
            form_data=submitted_form_data,
        )
        return response
    except DataSourceUnavailableError as exc:
        flash(str(exc), "danger")
        response = _render_new_experiment(
            status_code=503, form_data=submitted_form_data
        )
        persist_form_state(
            response,
            cookie_name=_EXPERIMENT_FORM_COOKIE,
            form_data=submitted_form_data,
        )
        return response
    response = redirect(url_for("experiments.detail", experiment_id=experiment_id))
    clear_form_state(response, cookie_name=_EXPERIMENT_FORM_COOKIE)
    return response


@bp.post("/bulk")
def create_bulk_experiment():
    submitted_form_data = {
        "bulk_mode": request.form.get("bulk_mode", "all_algorithms_for_symbol"),
        "symbol": request.form.get("symbol", ""),
        "symbols_text": request.form.get("symbols_text", ""),
        "alg_key": request.form.get("alg_key", ""),
        "skip_non_executable_defaults": request.form.get(
            "skip_non_executable_defaults", "false"
        ),
        "start_date": request.form.get("start_date", ""),
        "start_time": request.form.get("start_time", ""),
        "end_date": request.form.get("end_date", ""),
        "end_time": request.form.get("end_time", ""),
        "notes": request.form.get("notes", ""),
    }
    service = current_app.extensions["bulk_experiment_service"]
    try:
        if submitted_form_data["bulk_mode"] == "all_algorithms_for_symbol":
            result = service.submit_all_algorithms_for_symbol(
                symbol=submitted_form_data["symbol"],
                start_date=submitted_form_data["start_date"],
                start_time=submitted_form_data["start_time"],
                end_date=submitted_form_data["end_date"],
                end_time=submitted_form_data["end_time"],
                notes=submitted_form_data["notes"],
                skip_non_executable_defaults=(
                    submitted_form_data["skip_non_executable_defaults"] == "true"
                ),
            )
        elif submitted_form_data["bulk_mode"] == "single_algorithm_for_symbols":
            result = service.submit_single_algorithm_for_symbols(
                alg_key=submitted_form_data["alg_key"],
                symbols_text=submitted_form_data["symbols_text"],
                start_date=submitted_form_data["start_date"],
                start_time=submitted_form_data["start_time"],
                end_date=submitted_form_data["end_date"],
                end_time=submitted_form_data["end_time"],
                notes=submitted_form_data["notes"],
            )
        else:
            raise ValueError(
                f"Unsupported bulk submission mode: {submitted_form_data['bulk_mode']}"
            )
    except ValueError as exc:
        flash(str(exc), "danger")
        response = _render_bulk_experiment(
            status_code=400, form_data=submitted_form_data
        )
        persist_form_state(
            response,
            cookie_name=_BULK_EXPERIMENT_FORM_COOKIE,
            form_data=submitted_form_data,
        )
        return response
    success_message = (
        f"Bulk submission created {result.created_count} queued experiments."
    )
    if result.skipped_count:
        skipped_list = ", ".join(result.skipped_algorithms)
        success_message = (
            f"{success_message} Skipped {result.skipped_count} algorithms with "
            f"non-executable default params: {skipped_list}."
        )
    flash(success_message, "success")
    response = redirect(url_for("experiments.history"))
    clear_form_state(response, cookie_name=_BULK_EXPERIMENT_FORM_COOKIE)
    return response


@bp.get("/<experiment_id>")
def detail(experiment_id: str):
    payload = current_app.extensions["experiment_service"].get_experiment_detail(
        experiment_id
    )
    if payload is None:
        abort(404)
    payload["experiment"] = _decorate_experiment(payload["experiment"])
    payload["experiment_runtime_payload"] = _serialize_experiment_runtime(
        {
            **payload["experiment"],
            **dict(payload.get("queue_overview", {}).get("queue_summary") or {}),
        }
    )
    return render_template("experiments/detail.html", **payload)


@bp.get("/<experiment_id>/compare")
def compare(experiment_id: str):
    payload = current_app.extensions["experiment_service"].get_experiment_detail(
        experiment_id
    )
    if payload is None:
        abort(404)
    payload["experiment"] = _decorate_experiment(payload["experiment"])
    return render_template("experiments/compare.html", **payload)
