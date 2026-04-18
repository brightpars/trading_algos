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

bp = Blueprint("home", __name__)


@bp.get("/")
def home():
    settings = current_app.extensions[
        "data_source_settings_service"
    ].get_effective_settings()
    return render_template("home.html", data_source_settings=settings)


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
    return redirect(url_for("home.home"))


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


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "app": current_app.name})
