from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from trading_algos.configuration.serialization import configuration_from_dict
from trading_algos.configuration.validation import validate_configuration_payload

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/algorithms")
def algorithms():
    return jsonify(current_app.extensions["algorithm_catalog_service"]())


def _normalize_validation_errors(message: str) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for part in [item.strip() for item in message.split(";") if item.strip()]:
        if part.startswith("node "):
            node_parts = part.split(" ", 2)
            node_id = node_parts[1] if len(node_parts) > 1 else ""
            normalized.append({"scope": "node", "node_id": node_id, "message": part})
            continue
        normalized.append({"scope": "global", "message": part})
    return normalized


@bp.post("/configurations/validate")
def validate_configuration():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {
                "ok": False,
                "errors": [
                    {
                        "scope": "global",
                        "message": "Configuration payload must be a JSON object.",
                    }
                ],
            }
        ), 400
    try:
        normalized = validate_configuration_payload(configuration_from_dict(payload))
    except ValueError as exc:
        return (
            jsonify({"ok": False, "errors": _normalize_validation_errors(str(exc))}),
            400,
        )
    return jsonify(
        {
            "ok": True,
            "configuration": normalized.to_dict(),
            "compatibility": normalized.compatibility_metadata.to_dict(),
        }
    )


@bp.get("/experiments/<experiment_id>")
def experiment(experiment_id: str):
    payload = current_app.extensions["experiment_service"].get_experiment_detail(
        experiment_id
    )
    if payload is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(payload)


@bp.get("/configurations/<draft_id>")
def configuration(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        return jsonify({"error": "not found"}), 404
    payload["publication_records"] = current_app.extensions[
        "configuration_publish_service"
    ].list_records_for_draft(draft_id)
    return jsonify(payload)
