from pathlib import Path

from flask import Blueprint, current_app, jsonify, make_response, redirect, render_template, request, session, url_for

from app.models import Alert, CleanLog, db
from app.services.analytics import get_alerts, get_dashboard_summary, logs_to_csv, query_logs
from app.services.anomaly import detect_anomalies
from app.services.auth import authenticate, login_required
from app.services.collector import ingest_directory
from app.services.cleaning import clean_logs
from app.services.importer import import_dataframe
from app.services.log_parser import parse_log_file
from app.services.sample_data import generate_sample_logs, write_sample_files
from app.services.status import get_demo_report, get_system_status


bp = Blueprint("main", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        user = authenticate(request.form.get("username", ""), request.form.get("password", ""))
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            session["display_name"] = user.display_name
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        error = "用户名或密码错误"
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", active="dashboard")


@bp.route("/import", methods=["GET", "POST"])
@login_required
def import_page():
    message = ""
    if request.method == "POST":
        if "sample" in request.form:
            rows = int(request.form.get("rows", 1200))
            df = clean_logs(generate_sample_logs(rows, seed=42))
            result = import_dataframe(df, source="test-data")
            message = f"已生成并导入 {result['inserted']} 条测试日志。"
        elif "file" in request.files:
            upload = request.files["file"]
            if upload.filename:
                upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
                upload_dir.mkdir(parents=True, exist_ok=True)
                path = upload_dir / upload.filename
                upload.save(path)
                df = clean_logs(parse_log_file(path))
                result = import_dataframe(df, source=upload.filename)
                message = f"已导入 {result['inserted']} 条日志。"
    return render_template("import.html", active="import", message=message)


@bp.route("/logs")
@login_required
def logs_page():
    return render_template("logs.html", active="logs")


@bp.route("/analysis")
@login_required
def analysis_page():
    return render_template("analysis.html", active="analysis")


@bp.route("/anomalies", methods=["GET", "POST"])
@login_required
def anomalies_page():
    message = ""
    if request.method == "POST":
        result = detect_anomalies()
        message = f"检测完成：规则告警 {result['rule_alerts']} 条，机器学习标记 {result['ml_flagged']} 条。"
    return render_template("anomalies.html", active="anomalies", message=message)


@bp.route("/report")
@login_required
def report_page():
    return render_template("report.html", active="report")


@bp.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/api/dashboard")
@login_required
def api_dashboard():
    return jsonify(get_dashboard_summary())


@bp.route("/api/system/status")
@login_required
def api_system_status():
    return jsonify(get_system_status())


@bp.route("/api/report")
@login_required
def api_report():
    return jsonify(get_demo_report())


@bp.route("/api/collect/run", methods=["POST"])
@login_required
def api_collect_run():
    return jsonify(ingest_directory(current_app.config["INGEST_FOLDER"]))


@bp.route("/api/logs")
@login_required
def api_logs():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    items, total, total_pages = query_logs(request.args, page=page, per_page=per_page)
    return jsonify({"items": items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages})


@bp.route("/api/logs/export")
@login_required
def api_logs_export():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    csv_text = logs_to_csv(request.args, page=page, per_page=per_page)
    response = make_response(csv_text)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="campus_logs_page_{page}.csv"'
    return response


@bp.route("/api/anomalies")
@login_required
def api_anomalies():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 30))
    items, total, total_pages = get_alerts(page=page, per_page=per_page)
    return jsonify({"items": items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages})


@bp.route("/api/sample-files", methods=["POST"])
@login_required
def api_sample_files():
    files = write_sample_files(current_app.config["SAMPLE_FOLDER"], rows=int(request.form.get("rows", 120)))
    return jsonify({suffix: str(path) for suffix, path in files.items()})


@bp.route("/api/reset", methods=["POST"])
@login_required
def api_reset():
    CleanLog.query.delete()
    Alert.query.delete()
    db.session.commit()
    return redirect(url_for("main.import_page"))
