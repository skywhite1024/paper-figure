"""Refresh paper-scoped outputs; optionally publish checked regenerated files."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from paper_figure.outputs import refresh_output, publish_build, add_paper, add_papers
from paper_figure.model import ValidationError

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-build', type=Path, help='Build root containing paper-scoped export directories')
    parser.add_argument('--output', type=Path, default=ROOT / 'output')
    parser.add_argument('--paper', action='append', help='Limit --from-build to specified paper slug (repeatable)')
    parser.add_argument('--add-paper', type=Path, action='append', help='Complete new paper-scoped candidate folder to validate and register')
    args = parser.parse_args()
    if args.add_paper and args.from_build:
        parser.error('--add-paper and --from-build are mutually exclusive')
    if args.paper and not args.from_build:
        parser.error('--paper requires --from-build')
    try:
        result = (add_papers(ROOT, args.add_paper, args.output) if args.add_paper else
                  publish_build(ROOT, args.from_build, args.output, args.paper) if args.from_build else
                  refresh_output(ROOT, args.output))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValidationError) as exc:
        parser.exit(2, f'error: {exc}\n')

if __name__ == '__main__':
    main()
