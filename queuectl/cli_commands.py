import json
from .db import DB
from .worker import start_workers, stop_workers
from .utils import load_pids

def cmd_enqueue(args):
    db = DB()
    try:
        job = json.loads(args.job_json)
    except json.JSONDecodeError:
        print('Invalid JSON')
        return
    job_id = db.enqueue(job)
    print(f'Enqueued job {job_id}')


def cmd_status(args):
    db = DB()
    stats = db.get_stats()
    pids = load_pids()
    print('Job states:')
    for s in ['pending','processing','failed','completed','dead']:
        print(f'  {s}: {stats.get(s,0)}')
    print(f'Background worker PIDs: {pids}')


def cmd_list(args):
    db = DB()
    jobs = db.list_jobs(state=args.state)
    for j in jobs:
        print(json.dumps(j))


def cmd_worker_start(args):
    start_workers(args.count, daemon=args.daemon, job_timeout=args.timeout)


def cmd_worker_stop(args):
    stop_workers()


def cmd_dlq_list(args):
    db = DB()
    jobs = db.list_jobs(state='dead')
    for j in jobs:
        print(json.dumps(j))


def cmd_dlq_retry(args):
    db = DB()
    ok = db.retry_dead(args.job_id)
    if ok:
        print('Job retried')
    else:
        print('Job not found in DLQ')


def cmd_config_set(args):
    db = DB()
    db.set_config(args.key, args.value)
    print('OK')


def cmd_config_get(args):
    db = DB()
    val = db.get_config(args.key)
    if val is None:
        print('Not set')
    else:
        print(val)

def cmd_reset(args):
    confirm = input("This will stop all workers and delete all jobs. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Reset cancelled.")
        return
    stop_workers()
    db = DB()
    db.reset()
