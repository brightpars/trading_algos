from __future__ import annotations

from flask import Blueprint, abort, render_template

from trading_algos_dashboard.services.algorithm_catalog_service import (
    get_algorithm_catalog_entry,
    list_algorithm_catalog,
)

bp = Blueprint("algorithms", __name__, url_prefix="/algorithms")


@bp.get("")
def list_algorithms():
    return render_template("algorithms/list.html", algorithms=list_algorithm_catalog())


@bp.get("/<alg_key>")
def algorithm_detail(alg_key: str):
    try:
        algorithm = get_algorithm_catalog_entry(alg_key)
    except ValueError:
        abort(404)
    return render_template("algorithms/detail.html", algorithm=algorithm)
