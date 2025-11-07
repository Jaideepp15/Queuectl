import json, os
from datetime import datetime, timezone
from .config import PID_PATH

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def save_pids(pids):
    with open(PID_PATH, 'w') as f:
        json.dump({'pids': pids}, f)
    print(f"Saved PIDs to {PID_PATH}")


def load_pids():
    if not PID_PATH.exists():
        return []
    try:
        with open(PID_PATH) as f:
            data = json.load(f)
            return data.get('pids', [])
    except Exception:
        return []

def clear_pids():
    try:
        PID_PATH.unlink()
    except Exception:
        pass
