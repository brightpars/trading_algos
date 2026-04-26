from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from trading_algos.configuration.serialization import configuration_from_dict
from trading_algos.configuration.validation import validate_configuration_payload

bp = Blueprint("api", __name__, url_prefix="/api")


def _serialize_experiment_payload(payload: object) -> object:
    if isinstance(payload, dict):
        serialized = {
            key: _serialize_experiment_payload(value) for key, value in payload.items()
        }
        started_at = payload.get("started_at")
        parsed = _parse_runtime_datetime(started_at)
        if parsed is not None:
            serialized.setdefault("started_at_epoch_ms", int(parsed.timestamp() * 1000))
        return serialized
    if isinstance(payload, list):
        return [_serialize_experiment_payload(item) for item in payload]
    if isinstance(payload, datetime):
        if payload.tzinfo is None:
            payload = payload.replace(tzinfo=timezone.utc)
        return payload.astimezone(timezone.utc).isoformat()
    return payload


def _parse_runtime_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _parse_bool_arg(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


def _catalog_query_params() -> dict[str, object]:
    return {
        "implementation_status": str(request.args.get("status", "")).strip() or None,
        "category": str(request.args.get("category", "")).strip() or None,
        "catalog_type": str(request.args.get("catalog_type", "")).strip() or None,
        "advanced_label": str(request.args.get("advanced_label", "")).strip() or None,
        "search_text": str(request.args.get("search", "")).strip() or None,
    }


def _admin_catalog_query_params() -> dict[str, object]:
    page_value = str(request.args.get("page", "1")).strip()
    page_size_value = str(request.args.get("page_size", "25")).strip()
    try:
        page = int(page_value)
    except ValueError:
        page = 1
    try:
        page_size = int(page_size_value)
    except ValueError:
        page_size = 25
    return {
        "implementation_status": str(request.args.get("status", "")).strip() or None,
        "review_state": str(request.args.get("review_state", "")).strip() or None,
        "only_broken": _parse_bool_arg(request.args.get("only_broken")) is True,
        "only_unresolved": _parse_bool_arg(request.args.get("only_unresolved")) is True,
        "category": str(request.args.get("category", "")).strip() or None,
        "catalog_type": str(request.args.get("catalog_type", "")).strip() or None,
        "advanced_label": str(request.args.get("advanced_label", "")).strip() or None,
        "search_text": str(request.args.get("search", "")).strip() or None,
        "linked": _parse_bool_arg(request.args.get("linked")),
        "page": page,
        "page_size": page_size,
    }


def _get_json_object() -> Mapping[str, object] | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return None


def _backtrace_payload() -> tuple[Mapping[str, object] | None, Any]:
    payload = _get_json_object()
    if payload is None:
        return None, (
            jsonify(
                {
                    "error": "invalid_request",
                    "message": "Request body must be a JSON object.",
                }
            ),
            400,
        )
    return payload, None


def _backtrace_batch_payload() -> tuple[Mapping[str, object] | None, Any]:
    payload = _get_json_object()
    if payload is None:
        return None, (
            jsonify(
                {
                    "error": "invalid_request",
                    "message": "Request body must be a JSON object.",
                }
            ),
            400,
        )
    return payload, None


@bp.get("/algorithms")
def algorithms():
    return jsonify(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_algorithm_implementations()
    )


@bp.get("/algorithms/catalog")
def algorithm_catalog():
    return jsonify(
        current_app.extensions[
            "algorithm_catalog_service"
        ].list_catalog_entries_filtered(**_catalog_query_params())
    )


@bp.get("/algorithms/catalog/<entry_id>")
def algorithm_catalog_detail(entry_id: str):
    try:
        payload = current_app.extensions["algorithm_catalog_service"].get_catalog_entry(
            entry_id
        )
    except ValueError:
        return jsonify({"error": "not found"}), 404
    return jsonify(payload)


@bp.get("/algorithms/catalog/admin")
def algorithm_catalog_admin():
    payload = current_app.extensions[
        "algorithm_catalog_service"
    ].list_admin_catalog_entries(**_admin_catalog_query_params())
    return jsonify(payload)


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
    return jsonify(_serialize_experiment_payload(payload))


@bp.get("/experiments/queue")
def experiment_queue():
    payload = current_app.extensions["experiment_service"].get_queue_overview()
    return jsonify(_serialize_experiment_payload(payload))


@bp.get("/configurations/<draft_id>")
def configuration(draft_id: str):
    payload = current_app.extensions["configuration_builder_service"].get_draft_detail(
        draft_id
    )
    if payload is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(payload)


@bp.post("/backtraces")
def create_backtrace():
    payload, error_response = _backtrace_payload()
    if error_response is not None:
        return error_response
    try:
        run = current_app.extensions["backtrace_client_service"].submit_run(payload)
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": "validation_error",
                    "message": str(exc),
                }
            ),
            400,
        )
    return jsonify(run), 201


@bp.post("/backtraces/batch")
def create_backtrace_batch():
    payload, error_response = _backtrace_batch_payload()
    if error_response is not None:
        return error_response
    try:
        run = current_app.extensions["backtrace_client_service"].submit_batch(payload)
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": "validation_error",
                    "message": str(exc),
                }
            ),
            400,
        )
    return jsonify(run), 201


@bp.get("/backtraces")
def list_backtraces():
    payload = current_app.extensions["backtrace_client_service"].list_runs()
    return jsonify(payload)


@bp.get("/backtraces/<run_id>")
def backtrace_detail(run_id: str):
    payload = current_app.extensions["backtrace_client_service"].get_run(run_id)
    if payload is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(payload)
