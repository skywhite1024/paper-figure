"""Keep ordinary source labels live while fitting original PDF text bounds."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/buds-figure-2/buds-figure-2.json';s=json.loads(p.read_text())
for n in s['nodes']:
 if n['shape']=='text':
  n['font_size']*=.80;n['align']='center';n['y']+=1;n['no_wrap']=True
s['provenance']['text_repairs']='Ordinary labels are live Arial text fitted to original PDF bounds; embedded mathematical symbols remain original editable vector glyph paths.'
p.write_text(json.dumps(s,indent=2))
