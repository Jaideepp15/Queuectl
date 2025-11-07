import sqlite3, json, time
from .config import DB_PATH, DEFAULT_MAX_RETRIES, DEFAULT_BACKOFF_BASE
from .utils import now_iso

class DB:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        c = self.conn.cursor()
        c.execute('''PRAGMA journal_mode=WAL''')
        c.execute('''PRAGMA synchronous=NORMAL''')
        c.execute('PRAGMA busy_timeout=5000;')
        c.execute(f'''CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            state TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT {DEFAULT_MAX_RETRIES},
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            run_after INTEGER DEFAULT 0,
            last_error TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        # ensure default config exists
        c.execute('INSERT OR IGNORE INTO config(key,value) VALUES(?,?)', ('backoff_base', str(DEFAULT_BACKOFF_BASE)))
        c.execute('INSERT OR IGNORE INTO config(key,value) VALUES(?,?)', ('default_max_retries', str(DEFAULT_MAX_RETRIES)))
        self.conn.commit()

    def get_config(self, key, default=None):
        cur = self.conn.cursor()
        cur.execute('SELECT value FROM config WHERE key=?', (key,))
        r = cur.fetchone()
        return r['value'] if r else default

    def set_config(self, key, value):
        cur = self.conn.cursor()
        cur.execute('INSERT OR REPLACE INTO config(key,value) VALUES(?,?)', (key, str(value)))
        self.conn.commit()

    def get_next_job_id(self):
        cur = self.conn.cursor()
        # Retrieve current job counter
        cur.execute("SELECT value FROM config WHERE key='job_counter'")
        row = cur.fetchone()
        if row is None:
            next_id = 1
            cur.execute("INSERT INTO config(key, value) VALUES('job_counter', ?)", (str(next_id),))
        else:
            next_id = int(row['value']) + 1
            cur.execute("UPDATE config SET value=? WHERE key='job_counter'", (str(next_id),))
        self.conn.commit()
        return f"job{next_id}"


    def enqueue(self, job):
        cur = self.conn.cursor()
        now = now_iso()
        job = dict(job)

        # Always generate sequential job ID automatically
        job_id = self.get_next_job_id()
        job['id'] = job_id

        job.setdefault('state', 'pending')
        job.setdefault('attempts', 0)
        job.setdefault('max_retries', int(self.get_config('default_max_retries', DEFAULT_MAX_RETRIES)))
        job.setdefault('created_at', now)
        job.setdefault('updated_at', now)
        run_after = int(time.time())

        cur.execute('''INSERT INTO jobs(id,command,state,attempts,max_retries,created_at,updated_at,run_after,last_error)
                    VALUES(?,?,?,?,?,?,?,?,?)''', (
            job['id'], job['command'], job['state'], job['attempts'], job['max_retries'],
            job['created_at'], job['updated_at'], run_after, None
        ))

        self.conn.commit()
        return job['id']

    def get_stats(self):
        cur = self.conn.cursor()
        cur.execute("SELECT state, COUNT(*) as cnt FROM jobs GROUP BY state")
        rows = {r['state']: r['cnt'] for r in cur.fetchall()}
        return rows

    def list_jobs(self, state=None):
        cur = self.conn.cursor()
        if state:
            cur.execute('SELECT * FROM jobs WHERE state=? ORDER BY created_at', (state,))
        else:
            cur.execute('SELECT * FROM jobs ORDER BY created_at')
        return [dict(r) for r in cur.fetchall()]

    def _atomic_claim_job(self):
        # Find a pending job which is eligible (run_after <= now) and atomically set it to processing
        cur = self.conn.cursor()
        now = int(time.time())
        try:
            # Start exclusive transaction to avoid races
            cur.execute('BEGIN IMMEDIATE')
            cur.execute("SELECT * FROM jobs WHERE (state='pending' OR (state='failed' AND run_after <= ?)) ORDER BY created_at LIMIT 1", (now,))
            r = cur.fetchone()
            if not r:
                self.conn.commit()
                return None
            job = dict(r)
            job_id = job['id']
            updated_at = now_iso()
            cur.execute("UPDATE jobs SET state='processing', updated_at=? WHERE id=?", (now_iso(), job_id))
            if cur.rowcount != 1:
                # someone else claimed
                self.conn.commit()
                return None
            self.conn.commit()
            job['state'] = 'processing'
            job['updated_at'] = updated_at
            return job
        except sqlite3.OperationalError:
            self.conn.rollback()
            return None

    def mark_completed(self, job_id):
        cur = self.conn.cursor()
        cur.execute('UPDATE jobs SET state=?, updated_at=? WHERE id=?', ('completed', now_iso(), job_id))
        self.conn.commit()

    def mark_failed(self, job_id, attempts, max_retries, error_message, backoff_base):
        cur = self.conn.cursor()
        attempts = int(attempts)
        max_retries = int(max_retries)
        attempts += 1
        if attempts > max_retries:
            # move to dead
            cur.execute('UPDATE jobs SET state=?, attempts=?, updated_at=?, last_error=? WHERE id=?', ('dead', attempts, now_iso(), error_message, job_id))
            self.conn.commit()
            return 'dead'
        else:
            # compute backoff
            delay = int(backoff_base) ** attempts
            run_after = int(time.time()) + delay
            cur.execute('UPDATE jobs SET state=?, attempts=?, updated_at=?, run_after=?, last_error=? WHERE id=?', ('failed', attempts, now_iso(), run_after, error_message, job_id))
            self.conn.commit()
            return 'failed'

    def retry_dead(self, job_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM jobs WHERE id=? AND state="dead"', (job_id,))
        r = cur.fetchone()
        if not r:
            return False
        cur.execute('UPDATE jobs SET state=?, attempts=?, updated_at=?, run_after=?, last_error=? WHERE id=?', ('pending', 0, now_iso(), int(time.time()), None, job_id))
        self.conn.commit()
        return True

    def get_job(self, job_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM jobs WHERE id=?', (job_id,))
        r = cur.fetchone()
        return dict(r) if r else None
