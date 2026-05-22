from app import create_app
from app.models import CleanLog, IngestedFile, SystemEvent, db
from app.services.anomaly import detect_anomalies
from app.services.cleaning import clean_logs
from app.services.importer import import_dataframe
from app.services.sample_data import generate_sample_logs
from app.services.sample_data import write_sample_files


def seeded_app(tmp_path, rows=180):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "INGEST_FOLDER": tmp_path / "intake",
        }
    )
    with app.app_context():
        db.create_all()
        from app.services.auth import ensure_default_admin

        ensure_default_admin()
        import_dataframe(clean_logs(generate_sample_logs(rows, seed=31)), source="initial-demo")
        detect_anomalies()
    return app


def test_collect_directory_ingests_real_files_once(tmp_path):
    app = seeded_app(tmp_path)
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    write_sample_files(tmp_path / "intake", rows=12, seed=99)
    before = client.get("/api/system/status").get_json()["database"]["logs"]
    response = client.post("/api/collect/run")
    after = client.get("/api/system/status").get_json()["database"]["logs"]
    repeat = client.post("/api/collect/run")

    assert response.status_code == 200
    assert response.get_json()["inserted"] == 36
    assert after == before + 36
    assert repeat.get_json()["inserted"] == 0
    with app.app_context():
        assert db.session.query(SystemEvent).filter_by(event_type="collect").count() >= 1
        assert db.session.query(IngestedFile).count() == 3
        assert db.session.query(CleanLog).count() == 216


def test_report_endpoint_contains_metrics_and_test_cases(tmp_path):
    app = seeded_app(tmp_path)
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    response = client.get("/api/report")
    body = response.get_json()

    assert response.status_code == 200
    assert body["quality"]["accuracy"] >= 0.8
    assert body["quality"]["recall"] >= 0
    assert body["quality"]["f1"] >= 0
    assert body["performance"]["query_response_ms"] >= 0
    assert body["test_cases"]
    assert body["system_status"]["database"]["logs"] == 180


def test_status_endpoint_reports_recent_activity(tmp_path):
    app = seeded_app(tmp_path)
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})

    response = client.get("/api/system/status")
    body = response.get_json()

    assert response.status_code == 200
    assert body["runtime"]["status"] == "running"
    assert body["database"]["logs"] == 180
    assert body["recent_events"]
