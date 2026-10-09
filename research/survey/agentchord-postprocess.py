"""Fit unavailable source Chalkboard font using live Arial labels."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/agentchord-figure-2/agentchord-figure-2.json';s=json.loads(p.read_text())
for n in s['nodes']:
 if n['shape']=='text':n['font_size']*=.83;n['align']='center';n['no_wrap']=True
s['provenance']['text_repairs']='Live ordinary labels use fitted Arial instead of unavailable Chalkboard; mathematical source glyphs remain native vector outlines. This changes letterform style but preserves source wording, placement, color, diagram geometry and photographs.'
p.write_text(json.dumps(s,indent=2))
