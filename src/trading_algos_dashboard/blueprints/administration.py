from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
)

bp = Blueprint("administration", __name__, url_prefix="/administration")


@bp.get("")
def administration_home():
    administration_service = current_app.extensions["administration_service"]
    runtime_settings = current_app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()
    data_source_settings = current_app.extensions[
        "data_source_settings_service"
    ].get_effective_settings()
    cache_settings = current_app.extensions[
        "market_data_cache_settings_service"
    ].get_effective_settings()
    cache_stats = current_app.extensions["market_data_cache"].stats()
    return render_template(
        "administration/index.html",
        content_summary=administration_service.get_database_content_summary(),
        algorithm_catalog_summary=administration_service.get_algorithm_catalog_summary(),
        experiment_runtime_settings=runtime_settings,
        data_source_settings=data_source_settings,
        cache_settings=cache_settings,
        cache_stats=cache_stats,
    )


@bp.get("/experiment-runtime-settings")
def experiment_runtime_settings():
    runtime_settings = current_app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()
    data_source_settings = current_app.extensions[
        "data_source_settings_service"
    ].get_effective_settings()
    cache_settings = current_app.extensions[
        "market_data_cache_settings_service"
    ].get_effective_settings()
    cache_stats = current_app.extensions["market_data_cache"].stats()
    return render_template(
        "administration/experiment_runtime_settings.html",
        runtime_settings=runtime_settings,
        data_source_settings=data_source_settings,
        cache_settings=cache_settings,
        cache_stats=cache_stats,
    )


@bp.post("/experiment-runtime-settings")
def save_experiment_runtime_settings():
    runtime_settings_service = current_app.extensions[
        "experiment_runtime_settings_service"
    ]
    try:
        max_concurrent_experiments = int(
            request.form.get("max_concurrent_experiments", "1")
        )
        runtime_settings_service.save_settings(
            max_concurrent_experiments=max_concurrent_experiments
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("administration.experiment_runtime_settings"))

    flash(
        "administration: experiment runtime settings updated; "
        f"max_concurrent_experiments={max_concurrent_experiments}",
        "success",
    )
    return redirect(url_for("administration.experiment_runtime_settings"))


@bp.post("/data-source-settings")
def save_data_source_settings():
    ip = request.form.get("ip", "")
    port_raw = request.form.get("port", "")
    try:
        port = int(port_raw)
        current_app.extensions["data_source_settings_service"].save_settings(
            ip=ip,
            port=port,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
    else:
        flash("Data server settings saved.", "success")
    return redirect(url_for("administration.experiment_runtime_settings"))


@bp.post("/data-source-settings/check")
def check_data_source_settings():
    service = current_app.extensions["data_source_service"]
    form_ip = request.form.get("ip")
    form_port = request.form.get("port")
    original_resolver = service.endpoint_resolver
    if (
        form_ip is not None
        and form_port is not None
        and form_ip.strip()
        and form_port.strip()
    ):
        try:
            port_value = int(form_port)
        except ValueError:
            return jsonify(
                {"status": "error", "message": "Port must be an integer."}
            ), 400
        service.endpoint_resolver = lambda: (form_ip.strip(), port_value)
    try:
        payload = service.check_connection()
        return jsonify(payload)
    except (ValueError, DataSourceUnavailableError) as exc:
        return jsonify(
            {
                "status": "error",
                "message": str(exc),
                "endpoint": service._data_server_endpoint_label(),
            }
        ), 503
    finally:
        service.endpoint_resolver = original_resolver


@bp.post("/market-data-cache-settings")
def save_market_data_cache_settings():
    cache_settings_service = current_app.extensions[
        "market_data_cache_settings_service"
    ]
    market_data_cache = current_app.extensions["market_data_cache"]
    try:
        settings = cache_settings_service.save_settings(
            memory_enabled=request.form.get("memory_enabled") == "on",
            memory_max_entries=int(request.form.get("memory_max_entries", "100")),
            shared_enabled=request.form.get("shared_enabled") == "on",
            shared_max_entries=int(request.form.get("shared_max_entries", "1000")),
            shared_ttl_hours=int(request.form.get("shared_ttl_hours", "168")),
        )
        market_data_cache.configure(
            memory_enabled=settings["memory_enabled"],
            memory_max_entries=settings["memory_max_entries"],
            shared_enabled=settings["shared_enabled"],
            shared_max_entries=settings["shared_max_entries"],
            shared_ttl_hours=settings["shared_ttl_hours"],
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("administration.experiment_runtime_settings"))

    flash("administration: market data cache settings updated", "success")
    return redirect(url_for("administration.experiment_runtime_settings"))


@bp.post("/market-data-cache/clear-memory")
def clear_market_data_memory_cache():
    current_app.extensions["market_data_cache"].clear_memory()
    flash("administration: memory cache cleared", "success")
    return redirect(url_for("administration.experiment_runtime_settings"))


@bp.post("/market-data-cache/clear-shared")
def clear_market_data_shared_cache():
    deleted_count = current_app.extensions["market_data_cache"].clear_shared()
    flash(
        f"administration: shared cache cleared; deleted_entries={deleted_count}",
        "success",
    )
    return redirect(url_for("administration.experiment_runtime_settings"))


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


@bp.post("/algorithm-catalog/import")
def import_algorithm_catalog():
    import_service = current_app.extensions["algorithm_catalog_import_service"]
    administration_service = current_app.extensions["administration_service"]
    uploaded_file = request.files.get("catalog_file")
    if uploaded_file is None or not str(uploaded_file.filename or "").strip():
        flash(
            "administration: algorithm catalog import not executed; reason=missing_file",
            "warning",
        )
        return redirect(url_for("algorithms.list_algorithms"))
    filename = str(uploaded_file.filename).strip()
    if not filename.lower().endswith((".md", ".html", ".htm")):
        flash(
            "administration: algorithm catalog import not executed; reason=unsupported_file_type",
            "warning",
        )
        return redirect(url_for("algorithms.list_algorithms"))
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        flash(
            "administration: algorithm catalog import not executed; reason=file_not_utf8",
            "warning",
        )
        return redirect(url_for("algorithms.list_algorithms"))
    try:
        run = import_service.import_catalog(
            content=content,
            source_filename=filename,
            source_content_type=uploaded_file.content_type,
        )
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("algorithms.list_algorithms"))
    sync_summary = administration_service.rebuild_algorithm_catalog_links()
    flash(
        "administration: algorithm catalog imported; "
        f"source_filename={run['source_filename']} rows_seen={run['rows_seen']} rows_created={run['rows_created']} "
        f"rows_updated={run['rows_updated']} rows_unchanged={run['rows_unchanged']} "
        f"linked_count={sync_summary['linked_count']}",
        "success",
    )
    return redirect(
        url_for("administration.algorithm_catalog_import_detail", run_id=run["id"])
    )


@bp.post("/algorithm-catalog/sync-links")
def sync_algorithm_catalog_links():
    administration_service = current_app.extensions["administration_service"]
    summary = administration_service.rebuild_algorithm_catalog_links()
    flash(
        "administration: algorithm catalog links synced; "
        f"linked_count={summary['linked_count']} "
        f"missing_catalog_ref_count={summary['missing_catalog_ref_count']}",
        "success",
    )
    return redirect(url_for("algorithms.list_algorithms"))


@bp.post("/algorithm-catalog/delete-all")
def delete_algorithm_catalog_content():
    administration_service = current_app.extensions["administration_service"]
    confirmation_text = str(request.form.get("confirmation_text", "")).strip()
    try:
        summary = administration_service.delete_algorithm_catalog_content(
            confirmation_text=confirmation_text
        )
    except ValueError:
        flash(
            "administration: algorithm catalog deletion not executed; reason=invalid_confirmation_text",
            "warning",
        )
        return redirect(url_for("administration.administration_home"))
    flash(
        "administration: algorithm catalog deleted; "
        f"deleted_entries={summary['deleted_entries']} deleted_links={summary['deleted_links']}",
        "success",
    )
    return redirect(url_for("administration.administration_home"))


@bp.get("/algorithm-catalog")
def algorithm_catalog_admin():
    target_url = url_for("algorithms.list_algorithms")
    query_string = request.query_string.decode("utf-8").strip()
    if query_string:
        target_url = f"{target_url}?{query_string}"
    return redirect(target_url)


@bp.get("/algorithm-catalog/imports/<run_id>")
def algorithm_catalog_import_detail(run_id: str):
    administration_service = current_app.extensions["administration_service"]
    payload = administration_service.get_import_run_detail(run_id)
    return render_template(
        "administration/algorithm_catalog_import_detail.html", **payload
    )
