from __future__ import annotations

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

bp = Blueprint("algorithms", __name__, url_prefix="/algorithms")


@bp.get("")
def list_algorithms():
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]

    def _parse_page_arg(name: str) -> int:
        try:
            return int(request.args.get(name, "1"))
        except ValueError:
            return 1

    implementation_status = str(request.args.get("status", "")).strip() or None
    review_state = str(request.args.get("review_state", "")).strip() or None
    catalog_type = str(request.args.get("catalog_type", "")).strip() or None
    category = str(request.args.get("category", "")).strip() or None
    advanced_label = str(request.args.get("advanced_label", "")).strip() or None
    search_text = str(request.args.get("q", "")).strip() or None
    only_broken = str(request.args.get("only_broken", "")).strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }
    only_unresolved = str(request.args.get("only_unresolved", "")).strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }
    linked_value = str(request.args.get("linked", "")).strip().lower()
    linked = None
    if linked_value in {"true", "1", "yes"}:
        linked = True
    elif linked_value in {"false", "0", "no"}:
        linked = False

    return render_template(
        "algorithms/list.html",
        implementation_options=algorithm_catalog_service.list_algorithm_implementation_options(),
        **algorithm_catalog_service.get_catalog_page_data(
            implementation_status=implementation_status,
            review_state=review_state,
            only_broken=only_broken,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            only_unresolved=only_unresolved,
            search_text=search_text,
            unresolved_page=_parse_page_arg("unresolved_page"),
            broken_page=_parse_page_arg("broken_page"),
            review_page=_parse_page_arg("review_page"),
            queue_page=_parse_page_arg("page"),
        ),
    )


@bp.post("/new")
def create_algorithm():
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]
    catalog_values = {
        "name": request.form.get("name", ""),
        "category": request.form.get("category", ""),
        "subcategory": request.form.get("subcategory", ""),
        "advanced_label": request.form.get("advanced_label", ""),
        "best_use_horizon": request.form.get("best_use_horizon", ""),
        "home_suitability_score": request.form.get("home_suitability_score", "0"),
        "core_idea": request.form.get("core_idea", ""),
        "typical_inputs": request.form.get("typical_inputs", ""),
        "signal_style": request.form.get("signal_style", ""),
        "extended_implementation_details": request.form.get(
            "extended_implementation_details", ""
        ),
        "initial_reference": request.form.get("initial_reference", ""),
        "implementation_decision": request.form.get("implementation_decision", ""),
        "implementation_notes": request.form.get("implementation_notes", ""),
        "admin_annotations": request.form.get("admin_annotations", ""),
    }
    catalog_type = str(request.form.get("catalog_type", "algorithm")).strip()
    alg_impl_id = str(request.form.get("alg_impl_id", "")).strip() or None
    try:
        algorithm = algorithm_catalog_service.create_catalog_entry(
            catalog_values=catalog_values,
            catalog_type=catalog_type,
            alg_impl_id=alg_impl_id,
        )
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("algorithms.list_algorithms"))
    flash(
        "algorithm_catalog: algorithm created; "
        f"entry_id={algorithm['id']} review_state={algorithm['review_state_label']}",
        "success",
    )
    return redirect(
        url_for("algorithms.algorithm_detail", entry_id_or_slug=algorithm["slug"])
    )


@bp.get("/<entry_id_or_slug>")
def algorithm_detail(entry_id_or_slug: str):
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]
    try:
        algorithm = algorithm_catalog_service.get_catalog_entry(entry_id_or_slug)
    except ValueError:
        abort(404)
    return render_template(
        "algorithms/detail.html",
        algorithm=algorithm,
        review_states=algorithm_catalog_service.list_review_state_options(),
        implementation_options=algorithm_catalog_service.list_algorithm_implementation_options(),
    )


@bp.post("/<entry_id_or_slug>")
def update_algorithm_detail(entry_id_or_slug: str):
    algorithm_catalog_service = current_app.extensions["algorithm_catalog_service"]
    try:
        existing_algorithm = algorithm_catalog_service.get_catalog_entry(
            entry_id_or_slug
        )
    except ValueError:
        abort(404)
    catalog_values = {
        "name": request.form.get("name", existing_algorithm["name"]),
        "category": request.form.get("category", existing_algorithm["category"]),
        "subcategory": request.form.get(
            "subcategory", existing_algorithm["subcategory"]
        ),
        "advanced_label": request.form.get(
            "advanced_label", existing_algorithm["advanced_label"]
        ),
        "best_use_horizon": request.form.get(
            "best_use_horizon", existing_algorithm["best_use_horizon"]
        ),
        "home_suitability_score": request.form.get(
            "home_suitability_score", existing_algorithm["home_suitability_score"]
        ),
        "core_idea": request.form.get("core_idea", existing_algorithm["core_idea"]),
        "typical_inputs": request.form.get(
            "typical_inputs", existing_algorithm["typical_inputs"]
        ),
        "signal_style": request.form.get(
            "signal_style", existing_algorithm["signal_style"]
        ),
        "extended_implementation_details": request.form.get(
            "extended_implementation_details",
            existing_algorithm["extended_implementation_details"],
        ),
        "initial_reference": request.form.get(
            "initial_reference", existing_algorithm["initial_reference"]
        ),
        "implementation_decision": request.form.get(
            "implementation_decision", existing_algorithm["implementation_decision"]
        ),
        "implementation_notes": request.form.get(
            "implementation_notes", existing_algorithm["implementation_notes"]
        ),
        "admin_annotations": request.form.get(
            "admin_annotations", existing_algorithm["admin_annotations"]
        ),
    }
    review_state_value = str(request.form.get("review_state", "")).strip()
    review_state = review_state_value or None
    implementation_id_value = request.form.get("alg_impl_id")
    implementation_id = None
    if implementation_id_value is not None:
        implementation_id = str(implementation_id_value).strip()
    try:
        algorithm = algorithm_catalog_service.update_catalog_entry(
            entry_id_or_slug,
            catalog_values=catalog_values,
            review_state=review_state,
            link_notes=None,
            implementation_id=implementation_id,
        )
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(
            url_for("algorithms.algorithm_detail", entry_id_or_slug=entry_id_or_slug)
        )
    flash(
        "algorithm_catalog: algorithm updated; "
        f"entry_id={algorithm['id']} review_state={algorithm['review_state_label']}",
        "success",
    )
    return redirect(
        url_for("algorithms.algorithm_detail", entry_id_or_slug=algorithm["slug"])
    )
