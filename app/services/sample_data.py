from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


USER_TYPES = ["student", "teacher", "visitor"]
PROTOCOLS = ["HTTPS", "HTTP", "TCP", "UDP", "DNS"]
CATEGORIES = ["study", "video", "social", "office", "game", "security", "unknown"]
APPLICATIONS = {
    "study": ["MOOC", "Library", "CNKI", "GitHub"],
    "video": ["Bilibili", "TencentVideo", "MeetingLive"],
    "social": ["WeChat", "QQ", "Weibo"],
    "office": ["Email", "OA", "CloudDrive"],
    "game": ["GameLobby", "Steam"],
    "security": ["SSH", "RDP", "PortProbe"],
    "unknown": ["UnknownApp"],
}
DEVICES = ["firewall", "router", "proxy", "ids"]


def generate_sample_logs(rows=1000, seed=42):
    rng = np.random.default_rng(seed)
    start = datetime(2026, 5, 1, 6, 0, 0)
    records = []

    for index in range(rows):
        user_type = rng.choice(USER_TYPES, p=[0.68, 0.22, 0.10])
        user_prefix = {"student": "stu", "teacher": "tea", "visitor": "vis"}[user_type]
        user_id = f"{user_prefix}{rng.integers(1, 180):03d}"
        category = rng.choice(CATEGORIES, p=[0.30, 0.20, 0.16, 0.15, 0.08, 0.04, 0.07])
        application = rng.choice(APPLICATIONS[category])
        protocol = rng.choice(PROTOCOLS, p=[0.46, 0.18, 0.15, 0.10, 0.11])
        port = {"HTTPS": 443, "HTTP": 80, "DNS": 53}.get(protocol, int(rng.choice([22, 25, 110, 3306, 8080])))
        hour_offset = int(rng.normal(160, 74))
        minute_offset = int(rng.integers(0, 60))
        timestamp = start + timedelta(hours=max(0, hour_offset), minutes=minute_offset)
        base_down = int(rng.lognormal(mean=15.2, sigma=1.0))
        base_up = int(rng.lognormal(mean=13.6, sigma=0.9))
        connections = int(max(1, rng.poisson(8)))

        if category == "video":
            base_down *= 4
        if user_type == "teacher" and category == "office":
            base_up *= 2

        record = {
            "user_id": user_id,
            "user_type": user_type,
            "ip_address": f"10.{rng.integers(1, 12)}.{rng.integers(0, 255)}.{rng.integers(2, 254)}",
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "target": f"{application.lower()}.campus.example",
            "category": category,
            "application": application,
            "protocol": protocol,
            "port": port,
            "upload_bytes": base_up,
            "download_bytes": base_down,
            "connection_count": connections,
            "device": rng.choice(DEVICES),
            "source_format": "generated",
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)
    anomaly_indices = list(range(0, min(rows, 18), 3))
    for offset, idx in enumerate(anomaly_indices):
        if idx >= len(df):
            continue
        if offset % 3 == 0:
            df.loc[idx, ["connection_count", "category", "application", "protocol", "port"]] = [260, "security", "PortProbe", "TCP", 3389]
        elif offset % 3 == 1:
            df.loc[idx, ["download_bytes", "category", "application"]] = [950_000_000, "video", "Bilibili"]
        else:
            df.loc[idx, ["connection_count", "upload_bytes", "download_bytes"]] = [420, 180_000_000, 260_000_000]

    return df


def write_sample_files(directory, rows=120, seed=42):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    df = generate_sample_logs(rows, seed)
    files = {
        ".csv": directory / "campus_logs.csv",
        ".json": directory / "campus_logs.json",
        ".txt": directory / "campus_logs.txt",
    }
    df.to_csv(files[".csv"], index=False, encoding="utf-8")
    df.to_json(files[".json"], orient="records", force_ascii=False, indent=2)

    lines = []
    for row in df.to_dict("records"):
        lines.append(
            f"{row['timestamp']} {row['device']} user={row['user_id']} type={row['user_type']} "
            f"ip={row['ip_address']} target={row['target']} category={row['category']} "
            f"app={row['application']} proto={row['protocol']} port={row['port']} "
            f"up={row['upload_bytes']} down={row['download_bytes']} conn={row['connection_count']}"
        )
    files[".txt"].write_text("\n".join(lines), encoding="utf-8")
    return files
