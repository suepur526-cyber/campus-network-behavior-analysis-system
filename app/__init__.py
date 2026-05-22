from flask import Flask

from app.config import Config
from app.models import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    app.config["SAMPLE_FOLDER"].mkdir(parents=True, exist_ok=True)
    app.config["INGEST_FOLDER"].mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from app.routes import bp

    app.register_blueprint(bp)

    @app.cli.command("init-db")
    def init_db_command():
        from app.services.auth import ensure_default_admin

        db.create_all()
        ensure_default_admin()
        print("Initialized database.")

    @app.cli.command("seed-data")
    def seed_data_command():
        from app.services.cleaning import clean_logs
        from app.services.importer import import_dataframe
        from app.services.sample_data import generate_sample_logs

        df = clean_logs(generate_sample_logs(1200, seed=42))
        result = import_dataframe(df)
        print(f"Inserted {result['inserted']} sample logs.")

    @app.cli.command("detect-anomalies")
    def detect_anomalies_command():
        from app.services.anomaly import detect_anomalies

        result = detect_anomalies()
        print(result)

    return app
