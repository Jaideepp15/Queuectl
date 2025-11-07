#!/usr/bin/env python3
import argparse
from .cli_commands import cmd_enqueue,cmd_worker_start,cmd_worker_stop,cmd_list,cmd_status,cmd_dlq_retry,cmd_config_get,cmd_config_set,cmd_dlq_list


def build_parser():
    p = argparse.ArgumentParser(prog='queuectl')
    sub = p.add_subparsers(dest='cmd')

    enq = sub.add_parser('enqueue')
    enq.add_argument('job_json')
    enq.set_defaults(func=cmd_enqueue)

    worker = sub.add_parser('worker')
    wsub = worker.add_subparsers(dest='wcmd')
    wstart = wsub.add_parser('start')
    wstart.add_argument('--count', type=int, default=1)
    wstart.add_argument('--daemon', action='store_true', default=False)
    wstart.add_argument('--timeout', type=int, default=None, help='Job timeout seconds')
    wstart.set_defaults(func=cmd_worker_start)
    wstop = wsub.add_parser('stop')
    wstop.set_defaults(func=cmd_worker_stop)

    st = sub.add_parser('status')
    st.set_defaults(func=cmd_status)

    lst = sub.add_parser('list')
    lst.add_argument('--state', choices=['pending','processing','failed','completed','dead'], default=None)
    lst.set_defaults(func=cmd_list)

    dlq = sub.add_parser('dlq')
    dlq_sub = dlq.add_subparsers(dest='dlqcmd')
    dlq_list = dlq_sub.add_parser('list')
    dlq_list.set_defaults(func=cmd_dlq_list)
    dlq_retry = dlq_sub.add_parser('retry')
    dlq_retry.add_argument('job_id')
    dlq_retry.set_defaults(func=cmd_dlq_retry)

    cfg = sub.add_parser('config')
    cfg_sub = cfg.add_subparsers(dest='cfgcmd')
    cfg_set = cfg_sub.add_parser('set')
    cfg_set.add_argument('key')
    cfg_set.add_argument('value')
    cfg_set.set_defaults(func=cmd_config_set)
    cfg_get = cfg_sub.add_parser('get')
    cfg_get.add_argument('key')
    cfg_get.set_defaults(func=cmd_config_get)

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
