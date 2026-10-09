"""Initialize, inspect or evidence-update durable per-paper checkpoints.

The filename is also a stdlib module name. Preserve stdlib queue imports when
another research script uses concurrent.futures with this directory on sys.path.
"""
if __name__ == 'queue':
    import importlib.util
    import sys
    import sysconfig
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('queue', Path(sysconfig.get_path('stdlib')) / 'queue.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['queue'] = module
    spec.loader.exec_module(module)
else:
    import argparse
    import json
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))
    from paper_figure.model import ValidationError
    from paper_figure.queue import initialize_queue, queue_status, read_checkpoint, read_json, update_checkpoint

    def main(argv=None):
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--repository', type=Path, default=ROOT)
        commands = parser.add_subparsers(dest='command', required=True)
        init = commands.add_parser('init', help='Import catalog claims; never reset existing checkpoints')
        init.add_argument('--catalog', default='data/catalog.json')
        status = commands.add_parser('status', help='Read recorded counts or one checkpoint')
        status.add_argument('paper_id', nargs='?')
        status.add_argument('--verify-files', action='store_true', help='Rehash passed-stage evidence')
        update = commands.add_parser('update', help='Apply a JSON patch containing evidence')
        update.add_argument('paper_id')
        update.add_argument('evidence_file', type=Path)
        update.add_argument('--expected-revision', type=int)
        update.add_argument('--actor', default='operator')
        args = parser.parse_args(argv)
        try:
            if args.command == 'init':
                result = initialize_queue(args.repository, args.catalog)
            elif args.command == 'status':
                result = (read_checkpoint(args.repository, args.paper_id, args.verify_files) if args.paper_id
                          else queue_status(args.repository, args.verify_files))
            else:
                result = update_checkpoint(args.repository, args.paper_id, read_json(args.evidence_file),
                                           args.expected_revision, args.actor)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except (OSError, ValidationError) as exc:
            parser.exit(2, f'error: {exc}\n')

    if __name__ == '__main__':
        main()
