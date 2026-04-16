from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.get("")
def list_reports():
    reports = (
        current_app.extensions["result_repository"]
        .collection.find({})
        .sort("created_at", -1)
    )
    return render_template("reports/list.html", reports=list(reports))


@bp.get("/<experiment_id>")
def report_detail(experiment_id: str):
    payload = current_app.extensions["experiment_service"].get_experiment_detail(
        experiment_id
    )
    if payload is None:
        abort(404)
    return render_template("reports/detail.html", **payload)
