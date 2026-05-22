from app import create_app
from app.models import db


def test_app_routes_render_pages(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.create_all()
        from app.services.auth import ensure_default_admin

        ensure_default_admin()

    client = app.test_client()
    login = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    assert login.status_code == 200
    for path in ["/", "/import", "/logs", "/analysis", "/anomalies", "/report"]:
        response = client.get(path)
        assert response.status_code == 200
        assert b"CampusNet" in response.data


def test_health_endpoint(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_protected_pages_redirect_to_login(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.create_all()

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_logout_flow(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.create_all()
        from app.services.auth import ensure_default_admin

        ensure_default_admin()

    client = app.test_client()
    bad = client.post("/login", data={"username": "admin", "password": "wrong"})
    good = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    logout = client.get("/logout", follow_redirects=False)

    assert bad.status_code == 200
    assert "用户名或密码错误".encode() in bad.data
    assert good.status_code == 200
    assert "校园网用户行为分析系统".encode() in good.data
    assert logout.status_code == 302
