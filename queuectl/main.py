#!/usr/bin/env python3
import argparse
from .cli_commands import cmd_enqueue,cmd_worker_start,cmd_worker_stop,cmd_list,cmd_status,cmd_dlq_retry,cmd_config_get,cmd_config_set,cmd_dlq_list,cmd_reset


def build_parser():
    p = argparse.ArgumentParser(prog='queuectl')
    sub = p.add_subparsers(dest='cmd')

    enq = sub.add_parser('enqueue',help="Add a new job to the queue.")
    enq.add_argument('job_json',help="Job data in JSON format (e.g. '{\"command\":\"echo hi\",\"max-retries\":3,\"priority\":3}')")
    enq.set_defaults(func=cmd_enqueue)

    worker = sub.add_parser('worker',help="Manage worker processes.")
    wsub = worker.add_subparsers(dest='wcmd')
    wstart = wsub.add_parser('start',help="Start one or more workers.")
    wstart.add_argument('--count', type=int, default=1,help="Number of worker processes to start.")
    wstart.add_argument('--daemon', action='store_true', default=False,help="Run workers in background mode (default: foreground).")
    wstart.add_argument('--timeout', type=int, default=None, help='Job timeout seconds')
    wstart.set_defaults(func=cmd_worker_start)
    wstop = wsub.add_parser('stop',help="Stop all running workers.")
    wstop.set_defaults(func=cmd_worker_stop)

    st = sub.add_parser('status',help="Show job state summary and active workers.")
    st.set_defaults(func=cmd_status)

    lst = sub.add_parser('list',help="List jobs by state.")
    lst.add_argument('--state', choices=['pending','processing','failed','completed','dead'], default=None,help="Filter jobs by state (pending, processing, completed, failed, dead).")
    lst.set_defaults(func=cmd_list)

    dlq = sub.add_parser('dlq',help="Manage Dead Letter Queue (DLQ).")
    dlq_sub = dlq.add_subparsers(dest='dlqcmd')
    dlq_list = dlq_sub.add_parser('list',help="List all jobs in DLQ.")
    dlq_list.set_defaults(func=cmd_dlq_list)
    dlq_retry = dlq_sub.add_parser('retry',help="Retry a DLQ job by ID.")
    dlq_retry.add_argument('job_id',help="Job ID to retry (e.g. job5)")
    dlq_retry.set_defaults(func=cmd_dlq_retry)

    cfg = sub.add_parser('config',help="Manage queue configuration.")
    cfg_sub = cfg.add_subparsers(dest='cfgcmd')
    cfg_set = cfg_sub.add_parser('set',help="Set a configuration value.")
    cfg_set.add_argument('key',help="Configuration key (e.g. max-retries, backoff_base)")
    cfg_set.add_argument('value',help="Configuration value")
    cfg_set.set_defaults(func=cmd_config_set)
    cfg_get = cfg_sub.add_parser('get',help="Get a configuration value.")
    cfg_get.add_argument('key',help="Configuration key (e.g. max-retries, backoff_base)")
    cfg_get.set_defaults(func=cmd_config_get)

    reset = sub.add_parser("reset",help="Clear all jobs and reset queue system.")
    reset.set_defaults(func=cmd_reset)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, 'func'):
        parser.print_help()
        return
    args.func(args)

if __name__ == '__main__':
    main()
