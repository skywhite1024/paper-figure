"""Reviewed DDD font-substitution spacing adjustments; run after extraction."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'data/diagrams/divide-discover-deploy/divide-discover-deploy-figure-2.json'
s=json.loads(p.read_text())
for n in s['nodes']:
    if n['id']=='pdf-text-82-0': n['x']=735.989
    if n['id']=='pdf-text-154-0': n['label']='end  while';n['width']=125
s['provenance']['notes']+=' Source mathematical fonts are preserved as native glyph outlines (not live equations); two control-line spaces widened slightly for LibreOffice font substitution.'
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
