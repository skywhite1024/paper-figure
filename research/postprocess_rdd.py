"""Retain source Times BoldItal equation-reference typography."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'data/diagrams/rdd/rdd-figure-2.json';d=json.loads(p.read_text())
for n in d['nodes']:
    if n['shape']=='text' and 'BoldItal' in n.get('source_font',''):n['italic']=True
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
