"""Preserve typeable monospaced source reward-code example."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/curricullm-figure-1/curricullm-figure-1.json';s=json.loads(p.read_text())
for n in s['nodes']:
 if n.get('source_font','').startswith('SourceCodePro'):n['font_family']='Courier New'
s['provenance']['text_repairs']='SourceCodePro code excerpt remains live monospaced Courier New text; ordinary source labels remain live Arial.'
p.write_text(json.dumps(s,indent=2))
