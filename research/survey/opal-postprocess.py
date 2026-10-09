"""Remove invisible LaTeXiT metadata and fit source ordinary labels."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/opal-figure-2/opal-figure-2.json';s=json.loads(p.read_text())
s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('font_size',99)<.01)]
ns={n['id']:n for n in s['nodes']};remove=set()
for a,b,c,label in [(141,142,143,'(2) Offline training of task policy'),(173,174,175,'(1) Offline unsupervised primitive learning')]:
 g=[ns[f'pdf-text-{i}-0'] for i in [a,b,c]];g[0]['label']=label;g[0]['width']=g[-1]['x']+g[-1]['width']-g[0]['x'];remove.update(n['id'] for n in g[1:])
s['nodes']=[n for n in s['nodes'] if n['id'] not in remove]
for n in s['nodes']:
 if n['shape']=='text':n['font_size']*=.88;n['align']='center';n['no_wrap']=True
s['provenance']['text_repairs']='Invisible near-zero-size Courier LaTeXiT payload metadata removed; ordinary labels remain live text with merged source ligatures and fitted Arial metrics. Math remains original glyph outlines.'
p.write_text(json.dumps(s,indent=2))
