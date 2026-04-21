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


def _parse_initial_payload(raw_payload: str) -> dict[str, object] | None:
    if not raw_payload.strip():
        return None
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _build_builder_bootstrap(
    *,
    mode: str,
    form_action: str,
    submit_label: str,
    initial_payload: dict[str, object] | None,
    draft_id: str | None = None,
) -> dict[str, object]:
    return {
        "mode": mode,
        "draft_id": draft_id,
        "form_action": form_action,
        "submit_label": submit_label,
        "initial_payload": initial_payload,
    }


def _render_builder_page(
    *,
    mode: str,
    form_action: str,
    submit_label: str,
    title: str,
    raw_payload: str,
    draft_id: str | None = None,
    status_code: int = 200,
) -> tuple[str, int] | str:
    initial_payload = _parse_initial_payload(raw_payload)
    response = render_template(
        "configurations/new.html",
        page_title=title,
        submit_label=submit_label,
        form_action=form_action,
        draft_id=draft_id,
        form_data={"payload": raw_payload},
        builder_bootstrap=_build_builder_bootstrap(
            mode=mode,
            form_action=form_action,
            submit_label=submit_label,
            initial_payload=initial_payload,
            draft_id=draft_id,
        ),
    )
    return (response, status_code) if status_code != 200 else response


def _build_structure_lines(payload: dict[str, object]) -> list[str]:
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
            alg_param = node.get("alg_param", {})
            node_name = str(node.get("name") or alg_key or node_id)
            return [f"{prefix}{node_name} ({alg_key}) {alg_param}"]
        node_name = str(node.get("name") or node_type.upper())
        children = node.get("children") or []
        lines = [f"{prefix}{node_name} [{node_type.upper()}]"]
        if isinstance(children, list):
            for child_id in children:
                lines.extend(render(str(child_id), depth + 1))
        return lines

    root_node_id = str(payload.get("root_node_id", ""))
    return render(root_node_id, 0)


def _build_structure_tree(payload: dict[str, object]) -> dict[str, object] | None:
    nodes = payload.get("nodes") or []
    if not isinstance(nodes, list):
        return None
    nodes_by_id = {
        str(node.get("node_id")): node for node in nodes if isinstance(node, dict)
    }

    def render(node_id: str) -> dict[str, object] | None:
        node = nodes_by_id.get(node_id)
        if node is None:
            return None
        node_type = str(node.get("node_type", "unknown"))
        if node_type == "algorithm":
            return {
                "node_id": str(node.get("node_id", "")),
                "node_type": node_type,
                "name": str(node.get("name") or node.get("alg_key") or node_id),
                "description": str(node.get("description") or ""),
                "alg_key": str(node.get("alg_key") or ""),
                "alg_param": node.get("alg_param") or {},
                "buy_enabled": bool(node.get("buy_enabled", True)),
                "sell_enabled": bool(node.get("sell_enabled", True)),
                "children": [],
            }
        children = node.get("children") or []
        rendered_children = []
        if isinstance(children, list):
            for child_id in children:
                child_tree = render(str(child_id))
                if child_tree is not None:
                    rendered_children.append(child_tree)
        return {
            "node_id": str(node.get("node_id", "")),
            "node_type": node_type,
            "name": str(node.get("name") or node_type.upper()),
            "description": str(node.get("description") or ""),
            "children": rendered_children,
        }

    root_node_id = payload.get("root_node_id")
    if not isinstance(root_node_id, str) or not root_node_id:
        return None
    return render(root_node_id)


def _build_configuration_summary(payload: dict[str, object]) -> dict[str, object]:
    nodes = payload.get("nodes") or []
    if not isinstance(nodes, list):
        nodes = []
    algorithm_nodes = [
        node
        for node in nodes
        if isinstance(node, dict) and str(node.get("node_type", "")) == "algorithm"
    ]
    group_nodes = [
        node
        for node in nodes
        if isinstance(node, dict)
        and str(node.get("node_type", "")) in {"and", "or", "pipeline"}
    ]
    tags = payload.get("tags") or []
    return {
        "node_count": len(nodes),
        "algorithm_count": len(algorithm_nodes),
        "group_count": len(group_nodes),
        "root_node_id": str(payload.get("root_node_id", "")),
        "version": str(payload.get("version", "")),
        "status": str(payload.get("status", "draft")),
        "tags": [str(tag) for tag in tags] if isinstance(tags, list) else [],
    }


def _describe_revision_changes(
    current_payload: dict[str, object], previous_payload: dict[str, object] | None
) -> list[str]:
    if previous_payload is None:
        return ["Initial revision created."]

    changes: list[str] = []
    tracked_fields = ["name", "config_key", "version", "root_node_id"]
    for field in tracked_fields:
        current_value = current_payload.get(field)
        previous_value = previous_payload.get(field)
        if current_value != previous_value:
            changes.append(
                f"Changed {field} from {previous_value!r} to {current_value!r}."
            )

    current_nodes_raw = current_payload.get("nodes") or []
    previous_nodes_raw = previous_payload.get("nodes") or []
    current_nodes = current_nodes_raw if isinstance(current_nodes_raw, list) else []
    previous_nodes = previous_nodes_raw if isinstance(previous_nodes_raw, list) else []
    current_nodes_by_id = {
        str(node.get("node_id")): node
        for node in current_nodes
        if isinstance(node, dict)
    }
    previous_nodes_by_id = {
        str(node.get("node_id")): node
        for node in previous_nodes
        if isinstance(node, dict)
    }

    added_node_ids = sorted(set(current_nodes_by_id) - set(previous_nodes_by_id))
    removed_node_ids = sorted(set(previous_nodes_by_id) - set(current_nodes_by_id))
    for node_id in added_node_ids:
        node = current_nodes_by_id[node_id]
        changes.append(
            f"Added {node.get('node_type', 'node')} node {node.get('name') or node_id}."
        )
    for node_id in removed_node_ids:
        node = previous_nodes_by_id[node_id]
        changes.append(
            f"Removed {node.get('node_type', 'node')} node {node.get('name') or node_id}."
        )

    shared_node_ids = sorted(set(current_nodes_by_id) & set(previous_nodes_by_id))
    for node_id in shared_node_ids:
        current_node = current_nodes_by_id[node_id]
        previous_node = previous_nodes_by_id[node_id]
        if current_node.get("node_type") == "algorithm":
            current_param = current_node.get("alg_param") or {}
            previous_param = previous_node.get("alg_param") or {}
            if current_param != previous_param:
                changes.append(
                    f"Updated parameters for {current_node.get('name') or node_id} from {previous_param} to {current_param}."
                )
        if current_node.get("node_type") in {"and", "or", "pipeline"}:
            current_children = current_node.get("children") or []
            previous_children = previous_node.get("children") or []
            if current_children != previous_children:
                changes.append(
                    f"Changed children for {current_node.get('name') or node_id}."
                )

    return changes or ["No user-visible changes detected."]


def _decorate_revisions(revisions: list[dict[str, object]]) -> list[dict[str, object]]:
    decorated: list[dict[str, object]] = []
    ordered = list(reversed(revisions))
    previous_payload: dict[str, object] | None = None
    for revision in ordered:
        payload = revision.get("payload")
        payload_dict = payload if isinstance(payload, dict) else {}
        decorated.append(
            {
                **revision,
                "change_summary": _describe_revision_changes(
                    payload_dict,
                    previous_payload,
                ),
            }
        )
        previous_payload = payload_dict
    return list(reversed(decorated))


def _decorate_publication_records(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    decorated: list[dict[str, object]] = []
    for record in records:
        remote_status = str(record.get("remote_status") or "unknown")
        status_class = {
            "published": "success",
            "active": "success",
            "warning": "warning",
            "failed": "danger",
            "error": "danger",
        }.get(remote_status, "secondary")
        result = record.get("result") or {}
        result_dict = result if isinstance(result, dict) else {}
        decorated.append(
            {
                **record,
                "status_class": status_class,
                "status_label": remote_status.replace("_", " ").title(),
                "remote_version": result_dict.get("version")
                or record.get("remote_version"),
            }
        )
    return decorated


@bp.get("")
def list_configurations():
    drafts = current_app.extensions["configuration_builder_service"].list_drafts()
    return render_template("configurations/list.html", drafts=drafts)


@bp.get("/new")
def new_configuration():
    return _render_builder_page(
        mode="create",
        form_action=url_for("configurations.create_configuration"),
        submit_label="Save draft",
        title="New configuration draft",
        raw_payload="",
    )


@bp.post("")
def create_configuration():
    raw_payload = request.form.get("payload", "")
    try:
        payload = json.loads(raw_payload)
        if not isinstance(payload, dict):
            raise ValueError("configuration payload must be a JSON object")
        draft_id = current_app.extensions["configuration_builder_service"].create_draft(
            payload
        )
    except (json.JSONDecodeError, ValueError) as exc:
        flash(str(exc), "danger")
        return _render_builder_page(
            mode="create",
            form_action=url_for("configurations.create_configuration"),
            submit_label="Save draft",
            title="New configuration draft",
            raw_payload=raw_payload,
            status_code=400,
        )
    flash("Configuration draft created.", "success")
    return redirect(url_for("configurations.detail_configuration", draft_id=draft_id))


@bp.get("/<draft_id>/edit")
def edit_configuration(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        abort(404)
    raw_payload = json.dumps(payload["draft"]["payload"])
    return _render_builder_page(
        mode="edit",
        form_action=url_for("configurations.update_configuration", draft_id=draft_id),
        submit_label="Save changes",
        title="Edit configuration draft",
        raw_payload=raw_payload,
        draft_id=draft_id,
    )


@bp.post("/<draft_id>/edit")
def update_configuration(draft_id: str):
    existing = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if existing is None:
        abort(404)
    raw_payload = request.form.get("payload", "")
    try:
        payload = json.loads(raw_payload)
        if not isinstance(payload, dict):
            raise ValueError("configuration payload must be a JSON object")
        current_app.extensions["configuration_builder_service"].update_draft(
            draft_id,
            payload,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        flash(str(exc), "danger")
        return _render_builder_page(
            mode="edit",
            form_action=url_for(
                "configurations.update_configuration", draft_id=draft_id
            ),
            submit_label="Save changes",
            title="Edit configuration draft",
            raw_payload=raw_payload,
            draft_id=draft_id,
            status_code=400,
        )
    flash("Configuration draft updated.", "success")
    return redirect(url_for("configurations.detail_configuration", draft_id=draft_id))


@bp.get("/<draft_id>")
def detail_configuration(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        abort(404)
    draft_payload = payload["draft"]["payload"]
    payload["structure_lines"] = _build_structure_lines(draft_payload)
    payload["structure_tree"] = _build_structure_tree(draft_payload)
    payload["summary"] = _build_configuration_summary(draft_payload)
    payload["revisions"] = _decorate_revisions(payload["revisions"])
    payload["publication_records"] = _decorate_publication_records(
        current_app.extensions["configuration_publish_service"].list_records_for_draft(
            draft_id
        )
    )
    return render_template("configurations/detail.html", **payload)


@bp.post("/<draft_id>/validate-remote")
def validate_configuration_remote(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        abort(404)
    try:
        result = current_app.extensions[
            "configuration_publish_service"
        ].validate_remote(payload["draft"]["payload"])
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


@bp.post("/<draft_id>/delete")
def delete_configuration(draft_id: str):
    deleted = current_app.extensions["configuration_builder_service"].delete_draft(
        draft_id
    )
    if not deleted:
        abort(404)
    flash(f"Configuration draft deleted; draft_id={draft_id}", "success")
    return redirect(url_for("configurations.list_configurations"))
