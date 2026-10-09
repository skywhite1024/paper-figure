"""Fit unavailable source Chalkboard font using live Arial labels."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/agentchord-figure-2/agentchord-figure-2.json';s=json.loads(p.read_text())
ns={n['id']:n for n in s['nodes']};remove=set()
for inds in [[12,13],[14,15,16],[36,37],[100,101],[129,130]]:
 g=[ns[f'pdf-text-{i}-0'] for i in inds];n=g[0];n['label']=''.join(z['label'] for z in g);n['width']=g[-1]['x']+g[-1]['width']-n['x'];remove.update(z['id'] for z in g[1:])
s['nodes']=[n for n in s['nodes'] if n['id'] not in remove]
for n in s['nodes']:
 if n['shape']=='text':
  n['font_size']*=.83;n['align']='center';n['no_wrap']=True
  if n['id'] in [f'pdf-text-{i}-0' for i in [0,1,14,17,36,40,41,100,102]]:n['italic']=True
 if n['id'] in ['pdf-path-129','pdf-path-163']:
  w=n['width'];h=n['height'];n['commands']=[{'moveTo':{'x':1,'y':h}},{'lineTo':{'x':1,'y':h-7}},{'lineTo':{'x':w-1,'y':h-7}},{'lineTo':{'x':w-1,'y':h}},{'moveTo':{'x':w/2,'y':h-7}},{'lineTo':{'x':w/2,'y':0}}];n['fill']='none';n['stroke']='#202020';n['stroke_width']=2;n['stroke_opacity']=1
s['provenance']['path_repairs']='Reviewed arrow compounds split to preserve open heads without fill-parity seams; two lower execution braces redrawn as equivalent native stroked polylines.'
s['provenance']['text_repairs']='Live ordinary labels use fitted Arial instead of unavailable Chalkboard; mathematical source glyphs remain native vector outlines. This changes letterform style but preserves source wording, placement, color, diagram geometry and photographs.'
p.write_text(json.dumps(s,indent=2))
