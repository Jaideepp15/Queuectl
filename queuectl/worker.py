import os, time, subprocess, signal
from multiprocessing import Process
from .db import DB
from .config import DEFAULT_BACKOFF_BASE, POLL_INTERVAL
from .utils import save_pids, load_pids, now_iso, clear_pids

stop_signal = False

def worker_loop(worker_id, db_path, backoff_base, poll_interval=POLL_INTERVAL, job_timeout=None):
    db = DB(db_path)
    pid = os.getpid()
    print(f"[worker {worker_id}] pid={pid} started")

    def _handle_signals(signum, frame):
        global stop_signal
        stop_signal = True
        print(f"[worker {worker_id}] received stop signal, will exit after current job")

    signal.signal(signal.SIGTERM, _handle_signals)
    signal.signal(signal.SIGINT, _handle_signals)

    while not stop_signal:
        job = db._atomic_claim_job()
        if not job:
            time.sleep(poll_interval)
            continue
        job_id = job['id']
        command = job['command']
        print(f"[worker {worker_id}] picked job {job_id}: {command}")
        try:
            # run command
            # Use shell to support compound commands; in production consider safer execution
            completed = subprocess.run(command, shell=True, timeout=job_timeout)
            if completed.returncode == 0:
                db.mark_completed(job_id)
                print(f"[worker {worker_id}] job {job_id} completed")
            else:
                err = f"exit:{completed.returncode}"
                state = db.mark_failed(job_id, job['attempts'], job['max_retries'], err, backoff_base)
                print(f"[worker {worker_id}] job {job_id} failed -> {state} ({err})")
        except subprocess.TimeoutExpired:
            err = 'timeout'
            state = db.mark_failed(job_id, job['attempts'], job['max_retries'], err, backoff_base)
            print(f"[worker {worker_id}] job {job_id} timeout -> {state}")
        except Exception as e:
            err = str(e)
            state = db.mark_failed(job_id, job['attempts'], job['max_retries'], err, backoff_base)
            print(f"[worker {worker_id}] job {job_id} exception -> {state} ({err})")
    print(f"[worker {worker_id}] exiting")

def start_workers(count, daemon=False, job_timeout=None):
    db = DB()
    backoff_base = int(db.get_config('backoff_base', DEFAULT_BACKOFF_BASE))
    # spawn processes and detach
    pids = []
    for i in range(count):
        p = Process(target=worker_loop, args=(i, DB().path, backoff_base, POLL_INTERVAL, job_timeout))
        p.daemon = False
        p.start()
        pids.append(p.pid)
        print(f"Started worker pid={p.pid}")
    save_pids(pids)


def stop_workers():
    pids = load_pids()
    if not pids:
        print('No background workers found.')
        return
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f'Sent SIGTERM to pid {pid}')
        except ProcessLookupError:
            print(f'pid {pid} not found')
    # remove pidfile
    clear_pids()
