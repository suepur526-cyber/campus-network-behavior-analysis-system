from app import create_app
from app.models import Alert, CleanLog, db
from app.services.anomaly import detect_anomalies
from app.services.analytics import get_dashboard_summary, query_logs
from app.services.cleaning import clean_logs
from app.services.importer import import_dataframe
from app.services.sample_data import generate_sample_logs


def seeded_app(tmp_path, rows=260):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.create_all()
        from app.services.auth import ensure_default_admin

        ensure_default_admin()
        import_dataframe(clean_logs(generate_sample_logs(rows, seed=11)))
    return app


def test_analytics_summary_contains_required_dimensions(tmp_path):
    app = seeded_app(tmp_path)
    with app.app_context():
        summary = get_dashboard_summary()

    assert summary["totals"]["logs"] == 260
    assert summary["traffic_by_hour"]
    assert summary["protocol_distribution"]
    assert summary["category_distribution"]
    assert summary["user_type_distribution"]
    assert summary["top_users"]


def test_query_logs_filters_by_user_type_and_protocol(tmp_path):
    app = seeded_app(tmp_path)
    with app.app_context():
        rows, total, total_pages = query_logs({"user_type": "student", "protocol": "HTTPS"}, page=1, per_page=50)

    assert total >= len(rows)
    assert total_pages >= 1
    assert rows
    assert all(row["user_type"] == "student" for row in rows)
    assert all(row["protocol"] == "HTTPS" for row in rows)


def test_detect_anomalies_marks_logs_and_creates_alerts(tmp_path):
    app = seeded_app(tmp_path)
    with app.app_context():
        result = detect_anomalies()

        assert result["rule_alerts"] > 0
        assert result["ml_flagged"] > 0
        assert db.session.query(CleanLog).filter_by(is_anomaly=True).count() > 0
        assert db.session.query(Alert).count() > 0


def test_api_endpoints_return_data(tmp_path):
    app = seeded_app(tmp_path)
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    with app.app_context():
        detect_anomalies()

    dashboard = client.get("/api/dashboard")
    logs = client.get("/api/logs?user_type=student&page=1")
    anomalies = client.get("/api/anomalies")

    assert dashboard.status_code == 200
    assert dashboard.get_json()["totals"]["logs"] == 260
    assert logs.status_code == 200
    assert logs.get_json()["items"]
    assert anomalies.status_code == 200
    assert anomalies.get_json()["items"]


def test_logs_api_supports_pagination_and_export(tmp_path):
    app = seeded_app(tmp_path)
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    page_one = client.get("/api/logs?per_page=25&page=1")
    page_two = client.get("/api/logs?per_page=25&page=2")
    export_csv = client.get("/api/logs/export?per_page=10&page=1")

    assert page_one.status_code == 200
    assert page_one.get_json()["per_page"] == 25
    assert page_one.get_json()["page"] == 1
    assert page_one.get_json()["total_pages"] >= 1
    assert page_two.status_code == 200
    assert page_two.get_json()["page"] == 2
    assert export_csv.status_code == 200
    assert export_csv.headers["Content-Type"].startswith("text/csv")
    assert "attachment" in export_csv.headers["Content-Disposition"]


def test_anomalies_api_supports_pagination(tmp_path):
    app = seeded_app(tmp_path)
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    with app.app_context():
        detect_anomalies()

    response = client.get("/api/anomalies?page=1&per_page=12")
    assert response.status_code == 200
    body = response.get_json()
    assert body["page"] == 1
    assert body["per_page"] == 12
    assert body["total_pages"] >= 1
    assert body["items"]
