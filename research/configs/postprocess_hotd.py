"""Correct reviewed tiny icon hairlines using actual PDF paint bounds."""
import json
from pathlib import Path
import fitz
root=Path(__file__).resolve().parents[2]
config=json.loads((root/'research/configs/hotd.json').read_text())
p=root/'data/diagrams/hotd/hotd-figure-3.json';s=json.loads(p.read_text())
pdf=root/'build/sources/human-centric-open-future-task-discovery-formulation-benchmark-and-scalable-tree-based-search.pdf'
page=fitz.open(pdf)[3];log=page.get_bboxlog();byseq={d['seqno']:d for d in page.get_drawings()}
for node in s['nodes']:
    if node.get('source_seqno') in [10,11,23,25,51,52,54]:
        drawing=byseq[node['source_seqno']];seq=drawing['seqno']+(drawing['type']=='fs')
        painted=fitz.Rect(log[seq][1]);geometry=drawing['rect']
        padding=max(geometry.x0-painted.x0,geometry.y0-painted.y0,painted.x1-geometry.x1,painted.y1-geometry.y1)
        node['stroke_width']=2*padding*config['scale']
s['provenance']['notes']+=' Tiny robot icon hairline strokes were corrected from inspected source paint bounds; nested transform stroke estimates otherwise produced thick black outlines.'
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
