import datetime
import json
import os
from pathlib import Path

def load_json_cache(cache_path: Path):
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None


def save_json_cache(cache_path: Path, data):
    os.makedirs(cache_path.parent, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)


def build_cache_path(prefix: str, start: datetime.datetime, end: datetime.datetime) -> Path:
    cache_dir = Path(".cache")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{prefix}_{start.strftime('%Y_%m')}_{end.strftime('%Y-%m')}.json"
