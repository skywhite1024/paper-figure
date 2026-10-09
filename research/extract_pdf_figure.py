"""Extract a reviewed source crop to a draft native scene (never marks QA complete)."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--pdf', type=Path, required=True)
p.add_argument('--config', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
s = extract(a.pdf, json.loads(a.config.read_text()), a.out)
print(json.dumps({'id': s['id'], 'nodes': len(s['nodes']), 'warnings': s['provenance']['extraction_warnings']}, indent=2))
