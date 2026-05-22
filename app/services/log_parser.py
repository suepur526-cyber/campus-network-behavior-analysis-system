import json
import re
from pathlib import Path

import pandas as pd


TXT_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<device>\S+)\s+user=(?P<user_id>\S+)\s+type=(?P<user_type>\S+)\s+"
    r"ip=(?P<ip_address>\S+)\s+target=(?P<target>\S+)\s+category=(?P<category>\S+)\s+"
    r"app=(?P<application>\S+)\s+proto=(?P<protocol>\S+)\s+port=(?P<port>\d+)\s+"
    r"up=(?P<upload_bytes>-?\d+)\s+down=(?P<download_bytes>-?\d+)\s+conn=(?P<connection_count>\d+)"
)


def parse_log_file(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        df = pd.DataFrame(data)
    elif suffix in {".txt", ".log"}:
        df = _parse_txt(path)
    else:
        raise ValueError(f"Unsupported log format: {suffix}")
    df["source_format"] = suffix.lstrip(".")
    return df


def _parse_txt(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = TXT_PATTERN.match(line.strip())
        if match:
            rows.append(match.groupdict())
    return pd.DataFrame(rows)
