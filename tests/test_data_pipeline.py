from pathlib import Path

from app import create_app
from app.models import CleanLog, db
from app.services.cleaning import clean_logs
from app.services.importer import import_dataframe
from app.services.log_parser import parse_log_file
from app.services.sample_data import generate_sample_logs, write_sample_files


def test_sample_data_generation_has_required_scenarios():
    data = generate_sample_logs(240, seed=7)
    assert len(data) == 240
    assert {"student", "teacher", "visitor"} <= set(data["user_type"])
    assert (data["connection_count"] >= 200).any()
    assert (data["download_bytes"] >= 800_000_000).any()
    assert (data["port"] == 3389).any()


def test_parse_csv_json_and_txt(tmp_path):
    files = write_sample_files(tmp_path, rows=36, seed=4)
    for suffix in [".csv", ".json", ".txt"]:
        parsed = parse_log_file(files[suffix])
        assert len(parsed) == 36
        assert "user_id" in parsed.columns
        assert "timestamp" in parsed.columns


def test_clean_logs_normalizes_and_deduplicates():
    raw = generate_sample_logs(20, seed=2)
    raw.loc[0, "timestamp"] = "bad-time"
    raw.loc[1, "download_bytes"] = -5
    raw = raw._append(raw.iloc[2], ignore_index=True)

    cleaned = clean_logs(raw)

    assert len(cleaned) == 19
    assert cleaned["timestamp"].notna().all()
    assert (cleaned["download_bytes"] >= 0).all()
    assert cleaned["total_bytes"].gt(0).all()


def test_import_dataframe_persists_clean_logs(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.create_all()
        cleaned = clean_logs(generate_sample_logs(25, seed=1))
        result = import_dataframe(cleaned)

        assert result["inserted"] == 25
        assert db.session.query(CleanLog).count() == 25
