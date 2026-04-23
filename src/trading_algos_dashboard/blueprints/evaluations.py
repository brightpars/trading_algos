from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template, request


bp = Blueprint("evaluations", __name__, url_prefix="/evaluations")


def _default_filters() -> dict[str, str]:
    return {
        "symbol": "",
        "start_date": "",
        "start_time": "09:30",
        "end_date": "",
        "end_time": "16:00",
        "primary_metric": "cumulative_return",
    }


@bp.get("")
def index():
    comparable_cohorts = current_app.extensions[
        "evaluation_service"
    ].list_comparable_run_cohorts()
    return render_template(
        "evaluations/index.html",
        form_data=_default_filters(),
        comparable_cohorts=comparable_cohorts,
    )


@bp.get("/cohort")
def cohort():
    filters = {
        "symbol": request.args.get("symbol", ""),
        "start_date": request.args.get("start_date", ""),
        "start_time": request.args.get("start_time", "09:30"),
        "end_date": request.args.get("end_date", ""),
        "end_time": request.args.get("end_time", "16:00"),
        "primary_metric": request.args.get("primary_metric", "cumulative_return"),
    }
    try:
        payload = current_app.extensions["evaluation_service"].find_comparable_runs(
            symbol=filters["symbol"],
            start_date=filters["start_date"],
            start_time=filters["start_time"],
            end_date=filters["end_date"],
            end_time=filters["end_time"],
            primary_metric=filters["primary_metric"],
        )
    except ValueError as exc:
        abort(400, str(exc))
    return render_template(
        "evaluations/cohort.html",
        form_data=filters,
        **payload,
    )
