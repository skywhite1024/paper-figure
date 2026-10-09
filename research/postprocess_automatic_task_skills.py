"""Restore reviewed source serif labels with a portable Times-compatible face."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/diagrams/automatic-task-skills/automatic-task-skills-figure-1.json'
d=json.loads(p.read_text())
for n in d['nodes']:
    if n['shape']=='text' and any(f in n.get('source_font','') for f in ['Tinos','LiberationSerif','OpenSymbol']):
        n['font_family']='Times New Roman'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
