from __future__ import annotations

from flask import Blueprint, current_app, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/algorithms")
def algorithms():
    return jsonify(current_app.extensions["algorithm_catalog_service"]())


@bp.get("/experiments/<experiment_id>")
def experiment(experiment_id: str):
    payload = current_app.extensions["experiment_service"].get_experiment_detail(
        experiment_id
    )
    if payload is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(payload)
