"""Refresh paper-scoped outputs; optionally publish checked regenerated files."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from paper_figure.outputs import refresh_output, publish_build
from paper_figure.model import ValidationError

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-build', type=Path, help='Build root containing aspire/ and roboreact/ exports')
    parser.add_argument('--output', type=Path, default=ROOT / 'output')
    args = parser.parse_args()
    try:
        result = publish_build(ROOT, args.from_build, args.output) if args.from_build else refresh_output(ROOT, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValidationError) as exc:
        parser.exit(2, f'error: {exc}\n')

if __name__ == '__main__':
    main()
