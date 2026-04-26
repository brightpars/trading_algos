from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, cast

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

bp = Blueprint("backtraces", __name__, url_prefix="/backtraces")

_BACKTRACE_FORM_COOKIE = "trading_algos_dashboard_backtrace_form"


def _service() -> Any:
    return current_app.extensions["backtrace_dashboard_service"]


def _render_new_backtrace(
    *,
    status_code: int = 200,
    form_data: dict[str, str] | None = None,
) -> Response:
    effective_form_data = _service().build_form_data(
        saved_form_data=load_form_state(request.cookies.get(_BACKTRACE_FORM_COOKIE)),
        form_data=form_data,
    )
    return Response(
        render_template("backtraces/new.html", form_data=effective_form_data),
        status=status_code,
    )


def _json_pretty(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _decorate_run(run: dict[str, object]) -> dict[str, object]:
    payload = dict(run)
    request_payload = payload.get("request")
    full_result = payload.get("full_result")
    request_mapping = request_payload if isinstance(request_payload, Mapping) else {}
    result_mapping = full_result if isinstance(full_result, Mapping) else {}
    algorithm_params = request_mapping.get("algorithm_params")
    metadata = request_mapping.get("metadata")
    candles = request_mapping.get("candles")
    input_summary = payload.get("input_summary")
    input_summary_mapping = input_summary if isinstance(input_summary, Mapping) else {}

    payload["request_json"] = _json_pretty(request_payload or {})
    payload["full_result_json"] = _json_pretty(full_result or payload)
    payload["metadata"] = dict(metadata) if isinstance(metadata, Mapping) else {}
    payload["algorithm_params"] = (
        dict(algorithm_params) if isinstance(algorithm_params, Mapping) else {}
    )
    payload["candles"] = list(candles) if isinstance(candles, list) else []
    payload["signal_summary"] = dict(result_mapping.get("signal_summary") or {})
    payload["evaluation_summary"] = dict(result_mapping.get("evaluation_summary") or {})
    execution_steps = result_mapping.get("execution_steps")
    payload["execution_steps"] = (
        list(execution_steps) if isinstance(execution_steps, list) else []
    )
    payload["report"] = dict(result_mapping.get("report") or {})
    payload["chart_payload"] = dict(result_mapping.get("chart_payload") or {})
    candles_list = payload["candles"] if isinstance(payload["candles"], list) else []
    payload["candles_preview"] = candles_list[:3]
    payload["input_summary_text"] = ", ".join(
        [
            f"candles={input_summary_mapping.get('candle_count', 0)}",
            f"param_keys={len(payload['algorithm_params']) if isinstance(payload['algorithm_params'], Mapping) else 0}",
            f"metadata_keys={len(payload['metadata']) if isinstance(payload['metadata'], Mapping) else 0}",
        ]
    )
    return payload


@bp.get("")
def list_backtraces() -> str:
    payload = _service().list_runs()
    items = payload.get("items") if isinstance(payload, dict) else []
    if not isinstance(items, list):
        items = []
    runs = [_decorate_run(item) for item in items if isinstance(item, dict)]
    return render_template(
        "backtraces/list.html",
        runs=runs,
        count=len(runs),
    )


@bp.get("/new")
def new_backtrace() -> Response:
    return _render_new_backtrace()


@bp.post("")
def create_backtrace() -> Response:
    submitted_form_data = {
        "input_mode": request.form.get("input_mode", "inline_candles"),
        "algorithm_key": request.form.get("algorithm_key", ""),
        "symbol": request.form.get("symbol", ""),
        "algorithm_params_json": request.form.get("algorithm_params_json", "{}"),
        "candles_json": request.form.get("candles_json", "[]"),
        "data_source_kind": request.form.get("data_source_kind", "market_data_service"),
        "start_at": request.form.get("start_at", ""),
        "end_at": request.form.get("end_at", ""),
        "metadata_json": request.form.get("metadata_json", "{}"),
    }
    try:
        run = _service().submit_run(submitted_form_data)
    except ValueError as exc:
        flash(str(exc), "danger")
        form_response = _render_new_backtrace(
            status_code=400, form_data=submitted_form_data
        )
        persist_form_state(
            form_response,
            cookie_name=_BACKTRACE_FORM_COOKIE,
            form_data=submitted_form_data,
        )
        return form_response

    flash(f"Backtrace submitted; run_id={run['run_id']}", "success")
    redirect_response = cast(
        Response,
        redirect(url_for("backtraces.detail_backtrace", run_id=run["run_id"])),
    )
    clear_form_state(redirect_response, cookie_name=_BACKTRACE_FORM_COOKIE)
    return redirect_response


@bp.get("/<run_id>")
def detail_backtrace(run_id: str) -> str:
    run = _service().get_run(run_id)
    if run is None:
        abort(404)
    return render_template("backtraces/detail.html", run=_decorate_run(run))
