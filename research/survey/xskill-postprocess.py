"""Source ellipsis baseline fit for substituted Times font."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/xskill-figure-2/xskill-figure-2.json';s=json.loads(p.read_text())
for n in s['nodes']:
 if n['id']=='pdf-text-8-0':n['y']-=4
s['provenance']['text_repairs']='Ordinary labels remain live Times/Arial text; the three stylized function glyphs retain source outlines. Bottom distribution ellipsis baseline adjusted by one PDF point for substituted font metrics.'
p.write_text(json.dumps(s,indent=2))
