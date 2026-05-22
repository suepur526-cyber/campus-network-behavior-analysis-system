from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-net-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'campus_network.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    SAMPLE_FOLDER = BASE_DIR / "data" / "samples"
    INGEST_FOLDER = Path(os.getenv("INGEST_FOLDER", BASE_DIR / "data" / "ingest"))
