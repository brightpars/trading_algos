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


def _has_legacy_selected_algorithms(selected_algorithms: object) -> bool:
    if not isinstance(selected_algorithms, list):
        return False
    for algorithm in selected_algorithms:
        if not isinstance(algorithm, dict):
            return True
        if "alg_key" not in algorithm or "alg_param" not in algorithm:
            return True
    return False


def _experiment_form_defaults(catalog: list[dict[str, object]]) -> dict[str, str]:
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
        "has_legacy_selected_algorithms": "true"
        if _has_legacy_selected_algorithms(selected_algorithms)
        else "false",
    }


def _decorate_experiment(experiment: dict[str, object]) -> dict[str, object]:
    decorated = dict(experiment)
    decorated["has_legacy_selected_algorithms"] = _has_legacy_selected_algorithms(
        decorated.get("selected_algorithms")
    )
    started_at = decorated.get("started_at")
    if isinstance(started_at, datetime) and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
        decorated["started_at"] = started_at
    decorated["started_at_epoch_ms"] = (
        int(started_at.timestamp() * 1000) if isinstance(started_at, datetime) else None
    )
    decorated["is_running"] = decorated.get("status") == "running"
    decorated["is_cancelling"] = decorated.get("status") == "cancelling"
    decorated["is_failed"] = decorated.get("status") == "failed"
    decorated["is_cancelled"] = decorated.get("status") == "cancelled"
    return decorated


def _serialize_experiment_runtime(experiment: dict[str, object]) -> dict[str, object]:
    serialized = dict(experiment)
    for field in ("created_at", "updated_at", "started_at", "finished_at"):
        value = serialized.get(field)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            serialized[field] = value.astimezone(timezone.utc).isoformat()
    return serialized


def _cleanup_selected_algorithms_payload(
    selected_algorithms: object,
) -> tuple[list[dict[str, object]], int]:
    if not isinstance(selected_algorithms, list):
        raise ValueError("selected_algorithms must be a list")

    cleaned_algorithms: list[dict[str, object]] = []
    cleaned_count = 0
    catalog_service = current_app.extensions["algorithm_catalog_service"]

    for index, algorithm in enumerate(selected_algorithms, start=1):
        if isinstance(algorithm, dict):
            if "alg_key" not in algorithm or "alg_param" not in algorithm:
                raise ValueError(
                    f"Algorithm #{index} cannot be cleaned automatically because it is missing alg_key or alg_param"
                )
            cleaned_algorithms.append(
                {
                    "alg_key": algorithm["alg_key"],
                    "alg_param": algorithm["alg_param"],
                }
            )
            continue

        if isinstance(algorithm, str):
            catalog_entry = next(
                (item for item in catalog_service() if item.get("key") == algorithm),
                None,
            )
            if catalog_entry is None:
                raise ValueError(
                    f"Algorithm #{index} cannot be cleaned automatically because '{algorithm}' is not in the catalog"
                )
            cleaned_algorithms.append(
                {
                    "alg_key": algorithm,
                    "alg_param": catalog_entry["default_param"],
                }
            )
            cleaned_count += 1
            continue

        raise ValueError(
            f"Algorithm #{index} cannot be cleaned automatically because its value is unsupported"
        )

    return cleaned_algorithms, cleaned_count


def _recent_experiment_presets() -> list[dict[str, str]]:
    repo = current_app.extensions["experiment_repository"]
    experiments = repo.list_experiments()
    eligible_experiments = [
        experiment
        for experiment in experiments
        if isinstance(experiment.get("selected_algorithms"), list)
        and len(experiment.get("selected_algorithms", [])) > 0
    ]
    return [
        _serialize_recent_experiment(experiment)
        for experiment in eligible_experiments[:3]
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


def _render_new_experiment(
    *,
    status_code: int = 200,
    form_data: dict[str, str] | None = None,
) -> Response:
    catalog = current_app.extensions["algorithm_catalog_service"]()

    effective_form_data = _experiment_form_defaults(catalog)
    effective_form_data.update(
        load_form_state(request.cookies.get(_EXPERIMENT_FORM_COOKIE))
    )
    selected_configuration = _load_configuration_preset(request.args.get("draft_id"))
    if selected_configuration is not None:
        effective_form_data["configuration_json"] = selected_configuration[
            "configuration_json"
        ]
        effective_form_data["algorithms_json"] = "[]"
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
        ),
        status=status_code,
    )


@bp.get("")
def history():
    repo = current_app.extensions["experiment_repository"]
    experiments = [_decorate_experiment(item) for item in repo.list_experiments()]
    return render_template("experiments/history.html", experiments=experiments)


@bp.get("/new")
def new_experiment():
    return _render_new_experiment()


@bp.post("/<experiment_id>/cleanup-selected-algorithms")
def cleanup_selected_algorithms(experiment_id: str):
    repo = current_app.extensions["experiment_repository"]
    experiment = repo.get_experiment(experiment_id)
    if experiment is None:
        abort(404)

    selected_algorithms = experiment.get("selected_algorithms")
    if not isinstance(selected_algorithms, list) or len(selected_algorithms) == 0:
        flash("No saved selected algorithm config was found to clean.", "info")
        return redirect(request.referrer or url_for("experiments.history"))

    repo.clear_selected_algorithms(experiment_id)
    flash("Removed saved selected algorithm config.", "success")

    return redirect(request.referrer or url_for("experiments.history"))


@bp.post("/<experiment_id>/cancel")
def cancel_experiment(experiment_id: str):
    service = current_app.extensions["experiment_service"]
    try:
        was_requested = service.request_cancel(experiment_id)
    except ValueError:
        abort(404)

    if was_requested:
        flash("Experiment cancellation requested.", "info")
    else:
        flash("Experiment is no longer running and cannot be cancelled.", "warning")

    return redirect(url_for("experiments.detail", experiment_id=experiment_id))


@bp.post("/<experiment_id>/delete")
def delete_experiment(experiment_id: str):
    deleted = current_app.extensions["experiment_service"].delete_experiment(
        experiment_id
    )
    if not deleted:
        abort(404)
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
    }
    service = current_app.extensions["experiment_service"]
    try:
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
        payload["experiment"]
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
