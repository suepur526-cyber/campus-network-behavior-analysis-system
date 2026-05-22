import json

from app.models import CleanLog, SystemEvent, db


def import_dataframe(df, source="manual-import"):
    inserted = 0
    for row in df.to_dict("records"):
        log = CleanLog(
            user_id=row["user_id"],
            user_type=row["user_type"],
            ip_address=row["ip_address"],
            timestamp=row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
            target=row["target"],
            category=row["category"],
            application=row["application"],
            protocol=row["protocol"],
            port=int(row["port"]),
            upload_bytes=int(row["upload_bytes"]),
            download_bytes=int(row["download_bytes"]),
            total_bytes=int(row["total_bytes"]),
            connection_count=int(row["connection_count"]),
            device=row["device"],
            source_format=row["source_format"],
        )
        db.session.add(log)
        inserted += 1
    db.session.add(
        SystemEvent(
            event_type="import",
            message=f"导入 {inserted} 条日志",
            payload=json.dumps({"source": source, "inserted": inserted}, ensure_ascii=False),
        )
    )
    db.session.commit()
    return {"inserted": inserted}
