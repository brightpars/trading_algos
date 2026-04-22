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

bp = Blueprint("experiments", __name__, url_prefix="/experiments")

_EXPERIMENT_FORM_COOKIE = "trading_algos_dashboard_experiment_form"


def _experiment_form_defaults(catalog: list[dict[str, object]]) -> dict[str, str]:
    runtime_settings = current_app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()
    default_algorithms = "[]"
    if catalog:
        default_algorithms = json.dumps(
            [{"alg_key": catalog[0]["key"], "alg_param": catalog[0]["default_param"]}]
        )
    return {
        "symbol": "",
        "start_date": "",
        "start_time": "09:30",
        "end_date": "",
        "end_time": "16:00",
        "algorithms_json": default_algorithms,
        "configuration_json": "",
        "notes": "",
        "max_concurrent_experiments": str(
            runtime_settings["max_concurrent_experiments"]
        )
        if current_app
        else "1",
    }


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
        "algorithms_json": json.dumps(serialized_algorithms),
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


def _load_algorithm_preset(alg_key: str | None) -> dict[str, str] | None:
    if not alg_key:
        return None
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]
    try:
        algorithm_spec = algorithm_catalog_service.get_algorithm_implementation(alg_key)
    except ValueError:
        return None
    return {
        "algorithms_json": json.dumps(
            [
                {
                    "alg_key": str(algorithm_spec["key"]),
                    "alg_param": algorithm_spec.get("default_param", {}),
                }
            ]
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
        effective_form_data["configuration_json"] = selected_configuration[
            "configuration_json"
        ]
        effective_form_data["algorithms_json"] = "[]"
    elif selected_algorithm is not None:
        effective_form_data["algorithms_json"] = selected_algorithm["algorithms_json"]
        effective_form_data["configuration_json"] = ""
    if form_data is not None:
        effective_form_data.update(form_data)

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

    return Response(
        render_template(
            "experiments/new.html",
            algorithms=catalog,
            recent_experiments=_recent_experiment_presets(),
            selected_configuration=selected_configuration,
            form_data=effective_form_data,
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
    submitted_form_data = {
        "symbol": request.form.get("symbol", ""),
        "start_date": request.form.get("start_date", ""),
        "start_time": request.form.get("start_time", ""),
        "end_date": request.form.get("end_date", ""),
        "end_time": request.form.get("end_time", ""),
        "algorithms_json": request.form.get("algorithms_json", "[]"),
        "notes": request.form.get("notes", ""),
        "configuration_json": request.form.get("configuration_json", ""),
        "max_concurrent_experiments": str(
            current_app.config.get("EXPERIMENT_MAX_CONCURRENT_RUNS", 1)
        ),
    }
    service = current_app.extensions["experiment_service"]
    runtime_settings_service = current_app.extensions[
        "experiment_runtime_settings_service"
    ]
    try:
        max_concurrent_experiments = int(
            request.form.get("max_concurrent_experiments", "1")
        )
        runtime_settings_service.save_settings(
            max_concurrent_experiments=max_concurrent_experiments
        )
        algorithms = json.loads(submitted_form_data["algorithms_json"])
        configuration_payload = None
        if submitted_form_data["configuration_json"].strip():
            configuration_payload = json.loads(
                submitted_form_data["configuration_json"]
            )
        experiment_id = service.create_experiment(
            symbol=submitted_form_data["symbol"],
            start_date=submitted_form_data["start_date"],
            start_time=submitted_form_data["start_time"],
            end_date=submitted_form_data["end_date"],
            end_time=submitted_form_data["end_time"],
            algorithms=algorithms,
            configuration_payload=configuration_payload,
            notes=submitted_form_data["notes"],
        )
    except JSONDecodeError:
        flash("Algorithms JSON must be valid JSON.", "danger")
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
