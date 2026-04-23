from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
)

bp = Blueprint("home", __name__)


@bp.get("/")
def home():
    return render_template("home.html")


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "app": current_app.name})
