from __future__ import annotations

import json

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

bp = Blueprint("configurations", __name__, url_prefix="/configurations")


@bp.get("")
def list_configurations():
    drafts = current_app.extensions["configuration_builder_service"].list_drafts()
    return render_template("configurations/list.html", drafts=drafts)


@bp.get("/new")
def new_configuration():
    return render_template("configurations/new.html", form_data={"payload": ""})


@bp.post("")
def create_configuration():
    raw_payload = request.form.get("payload", "")
    try:
        payload = json.loads(raw_payload)
        draft_id = current_app.extensions["configuration_builder_service"].create_draft(
            payload
        )
    except (json.JSONDecodeError, ValueError) as exc:
        flash(str(exc), "danger")
        return render_template(
            "configurations/new.html",
            form_data={"payload": raw_payload},
        ), 400
    flash("Configuration draft created.", "success")
    return redirect(url_for("configurations.detail_configuration", draft_id=draft_id))


@bp.get("/<draft_id>")
def detail_configuration(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        abort(404)
    payload["publication_records"] = current_app.extensions[
        "configuration_publish_service"
    ].list_records_for_draft(draft_id)
    return render_template("configurations/detail.html", **payload)


@bp.post("/<draft_id>/validate-remote")
def validate_configuration_remote(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        abort(404)
    try:
        result = current_app.extensions["configuration_publish_service"].validate_remote(
            payload["draft"]["payload"]
        )
    except Exception as exc:
        flash(f"Remote validation failed: {exc}", "danger")
    else:
        compatibility = result.get("compatibility", {})
        flash(
            f"Remote validation ok. compatibility_state={compatibility.get('compatibility_state', 'unknown')}",
            "success",
        )
    return redirect(url_for("configurations.detail_configuration", draft_id=draft_id))


@bp.post("/<draft_id>/publish")
def publish_configuration(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        abort(404)
    try:
        result = current_app.extensions["configuration_publish_service"].publish(
            draft_id=draft_id,
            payload=payload["draft"]["payload"],
        )
    except Exception as exc:
        flash(f"Publish failed: {exc}", "danger")
    else:
        flash(
            f"Published configuration remote_config_id={result.get('config_id', 'unknown')}",
            "success",
        )
    return redirect(url_for("configurations.detail_configuration", draft_id=draft_id))
