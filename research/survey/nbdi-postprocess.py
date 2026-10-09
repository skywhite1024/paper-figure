"""Reviewed native label spacing and fit repair; run after PDF extraction."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/nbdi-figure-13/nbdi-figure-13.json';s=json.loads(p.read_text());nodes={n['id']:n for n in s['nodes']};remove=set()
for ids,label in [([30,31,32],'State-Action'),([33,34],'Novelty Module'),([281,282,283],'State-Action'),([284,285],'Novelty Module')]:
 group=[nodes[f'pdf-text-{i}-0'] for i in ids];n=group[0];right=max(z['x']+z['width'] for z in group);n['width']=right-n['x'];n['label']=label;remove.update(z['id'] for z in group[1:])
s['nodes']=[n for n in s['nodes'] if n['id'] not in remove]
for n in s['nodes']:
 if n['shape']!='text':continue
 n['font_size']*=.84;n['align']='center';n['y']+=1.4
s['provenance']['text_repairs']='Ordinary source Calibri labels remain typeable Arial text. Source split State-Action and Novelty Module fragments merged; font sizes reduced to retain original box fit. Mathematical labels remain exact glyph outlines.'
p.write_text(json.dumps(s,indent=2,ensure_ascii=False))
