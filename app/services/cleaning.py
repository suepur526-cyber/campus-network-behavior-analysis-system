import pandas as pd


REQUIRED_COLUMNS = [
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
    "connection_count",
    "device",
    "source_format",
]


def clean_logs(raw):
    df = raw.copy()
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = _default_for(column)

    df = df[REQUIRED_COLUMNS]
    for column in ["user_id", "user_type", "ip_address", "target", "category", "application", "protocol", "device", "source_format"]:
        df[column] = df[column].fillna(_default_for(column)).astype(str).str.strip()
        df.loc[df[column] == "", column] = _default_for(column)

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["timestamp"])

    for column in ["port", "upload_bytes", "download_bytes", "connection_count"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(_default_for(column)).astype(int)
        df.loc[df[column] < 0, column] = 0

    df.loc[df["port"] == 0, "port"] = 80
    df.loc[df["connection_count"] == 0, "connection_count"] = 1
    df["protocol"] = df["protocol"].str.upper()
    df["user_type"] = df["user_type"].str.lower()
    df["total_bytes"] = df["upload_bytes"] + df["download_bytes"]
    df = df.drop_duplicates(
        subset=["user_id", "ip_address", "timestamp", "target", "protocol", "port", "upload_bytes", "download_bytes"]
    )
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def _default_for(column):
    defaults = {
        "user_id": "unknown",
        "user_type": "student",
        "ip_address": "0.0.0.0",
        "timestamp": None,
        "target": "unknown.local",
        "category": "unknown",
        "application": "UnknownApp",
        "protocol": "TCP",
        "port": 80,
        "upload_bytes": 0,
        "download_bytes": 0,
        "connection_count": 1,
        "device": "gateway",
        "source_format": "unknown",
    }
    return defaults[column]
