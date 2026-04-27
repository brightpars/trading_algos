from __future__ import annotations

import json
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
    configuration_presets = _list_configuration_presets()
    recent_configuration_presets = _recent_configuration_presets(configuration_presets)
    decmakers = current_app.extensions[
        "algorithm_catalog_service"
    ].list_decmaker_implementations()
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
            configuration_presets=configuration_presets,
            recent_configuration_presets=recent_configuration_presets,
            decmakers=decmakers,
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

    service = current_app.extensions["experiment_service"]
    quick_builder_algorithms = _build_quick_builder_algorithms(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_algorithm_implementations()
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
