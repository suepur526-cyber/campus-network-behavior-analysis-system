from collections import Counter, defaultdict
import csv
import io
from datetime import datetime

from app.models import Alert, CleanLog


def get_dashboard_summary():
    logs = CleanLog.query.order_by(CleanLog.timestamp.asc()).all()
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
    total_bytes = sum(log.total_bytes for log in logs)
    anomaly_count = sum(1 for log in logs if log.is_anomaly)

    return {
        "totals": {
            "logs": len(logs),
            "users": len({log.user_id for log in logs}),
            "traffic_gb": round(total_bytes / 1024 / 1024 / 1024, 2),
            "anomalies": anomaly_count,
        },
        "traffic_by_hour": _traffic_by_hour(logs),
        "protocol_distribution": _count(logs, "protocol"),
        "category_distribution": _count(logs, "category"),
        "user_type_distribution": _count(logs, "user_type"),
        "application_distribution": _count(logs, "application", limit=8),
        "top_users": _top_users(logs),
        "anomaly_types": _anomaly_types(logs),
        "recent_alerts": [alert.to_dict() for alert in alerts],
    }


def query_logs(filters, page=1, per_page=20):
    query = CleanLog.query
    if filters.get("user_type"):
        query = query.filter(CleanLog.user_type == filters["user_type"])
    if filters.get("protocol"):
        query = query.filter(CleanLog.protocol == filters["protocol"].upper())
    if filters.get("is_anomaly") in {"true", "false"}:
        query = query.filter(CleanLog.is_anomaly == (filters["is_anomaly"] == "true"))
    if filters.get("keyword"):
        keyword = f"%{filters['keyword']}%"
        query = query.filter(
            CleanLog.user_id.like(keyword) | CleanLog.ip_address.like(keyword) | CleanLog.target.like(keyword)
        )
    if filters.get("start"):
        query = query.filter(CleanLog.timestamp >= datetime.fromisoformat(filters["start"]))
    if filters.get("end"):
        query = query.filter(CleanLog.timestamp <= datetime.fromisoformat(filters["end"]))

    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    items = (
        query.order_by(CleanLog.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [item.to_dict() for item in items], total, total_pages


def logs_to_csv(filters, page=1, per_page=20):
    rows, _, _ = query_logs(filters, page=page, per_page=per_page)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "id",
            "user_id",
            "user_type",
            "ip_address",
            "timestamp",
            "target",
            "category",
            "application",
            "protocol",
            "port",
            "upload_bytes",
            "download_bytes",
            "total_bytes",
            "connection_count",
            "device",
            "source_format",
            "is_anomaly",
            "anomaly_reason",
            "ml_score",
            "cluster_label",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def get_alerts(page=1, per_page=30):
    query = Alert.query.order_by(Alert.created_at.desc())
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return [item.to_dict() for item in items], total, total_pages


def _traffic_by_hour(logs):
    buckets = defaultdict(int)
    for log in logs:
        key = log.timestamp.strftime("%m-%d %H:00")
        buckets[key] += log.total_bytes
    return [{"time": key, "gb": round(value / 1024 / 1024 / 1024, 3)} for key, value in sorted(buckets.items())]


def _count(logs, attr, limit=None):
    counter = Counter(getattr(log, attr) for log in logs)
    rows = [{"name": key, "value": value} for key, value in counter.most_common(limit)]
    return rows


def _top_users(logs):
    traffic = defaultdict(int)
    counts = defaultdict(int)
    for log in logs:
        traffic[log.user_id] += log.total_bytes
        counts[log.user_id] += 1
    return [
        {"user_id": user, "traffic_mb": round(value / 1024 / 1024, 2), "visits": counts[user]}
        for user, value in sorted(traffic.items(), key=lambda item: item[1], reverse=True)[:10]
    ]


def _anomaly_types(logs):
    counter = Counter()
    for log in logs:
        if log.is_anomaly:
            for reason in (log.anomaly_reason or "异常行为").split("; "):
                counter[reason] += 1
    return [{"name": key, "value": value} for key, value in counter.most_common()]
