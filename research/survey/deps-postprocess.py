"""Fit original Minion/Calibri label metrics using editable installed fonts."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/deps-figure-1/deps-figure-1.json';s=json.loads(p.read_text())
for n in s['nodes']:
 if n['shape']=='text':
  n['font_size']*=.81;n['align']='center';n['no_wrap']=True
  if 'Policy' in n.get('label',''):n['font_family']='Times New Roman'
s['provenance']['text_repairs']='Original main policy labels remain live serif text; environment/compressed state labels remain live Arial. Fitted font sizes preserve source line bounds.'
p.write_text(json.dumps(s,indent=2))
