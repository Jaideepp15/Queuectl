from pathlib import Path
import os

# --- Global configuration ---
HOME = Path.home()
STATE_DIR = HOME / '.queuectl'
DB_PATH = STATE_DIR / 'jobs.db'
PID_PATH = STATE_DIR / 'pids.json'
DEFAULT_BACKOFF_BASE = 2
DEFAULT_MAX_RETRIES = 3
POLL_INTERVAL = 1.0

os.makedirs(STATE_DIR, exist_ok=True)
