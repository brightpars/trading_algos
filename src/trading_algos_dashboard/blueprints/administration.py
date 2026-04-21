from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, url_for

bp = Blueprint("administration", __name__, url_prefix="/administration")


@bp.get("")
def administration_home():
    administration_service = current_app.extensions["administration_service"]
    return render_template(
        "administration/index.html",
        content_summary=administration_service.get_database_content_summary(),
    )


@bp.post("/experiments/clear")
def clear_experiments():
    administration_service = current_app.extensions["administration_service"]
    deletion_summary = administration_service.clear_experiments()
    flash(
        "administration: experiments cleared; "
        f"deleted_experiments={deletion_summary['deleted_experiments']} "
        f"deleted_results={deletion_summary['deleted_results']}",
        "success",
    )
    return redirect(url_for("administration.administration_home"))


@bp.post("/results/clear")
def clear_results():
    administration_service = current_app.extensions["administration_service"]
    deleted_results = administration_service.clear_results()
    flash(
        f"administration: results cleared; deleted_results={deleted_results}",
        "success",
    )
    return redirect(url_for("administration.administration_home"))
