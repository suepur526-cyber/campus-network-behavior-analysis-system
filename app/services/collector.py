from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from app.models import IngestedFile, SystemEvent, db
from app.services.cleaning import clean_logs
from app.services.importer import import_dataframe
from app.services.log_parser import parse_log_file


def ingest_directory(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    supported = [".csv", ".json", ".txt", ".log"]
    processed = []
    inserted = 0

    existing_hashes = {row[0] for row in db.session.execute(select(IngestedFile.file_hash)).all()}
    existing_names = {row[0] for row in db.session.execute(select(IngestedFile.file_name)).all()}

    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in supported:
            continue
        file_hash = sha256(path)
        if file_hash in existing_hashes or path.name in existing_names:
            continue
        df = clean_logs(parse_log_file(path))
        result = import_dataframe(df, source=path.name)
        db.session.add(
            IngestedFile(
                file_name=path.name,
                file_path=str(path),
                file_hash=file_hash,
                row_count=result["inserted"],
                source_format=path.suffix.lower().lstrip("."),
            )
        )
        processed.append(path.name)
        inserted += result["inserted"]
        existing_hashes.add(file_hash)
        existing_names.add(path.name)

    if processed:
        db.session.add(
            SystemEvent(
                event_type="collect",
                message=f"接入目录采集 {len(processed)} 个文件，新增 {inserted} 条日志",
                payload=json.dumps({"directory": str(directory), "files": processed, "inserted": inserted}, ensure_ascii=False),
            )
        )
        db.session.commit()
    else:
        db.session.commit()

    return {"files": processed, "inserted": inserted}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
