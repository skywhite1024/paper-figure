"""Reproduce the inspected source figure, retaining typeable ordinary labels."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/ibol');a=p.parse_args()
c=json.loads((ROOT/'research/survey/unsupervised-skill-discovery-with-bottleneck-option-learning-config.json').read_text());s=extract(a.pdf,c,a.out)
for node in s['nodes']:
    if node['shape']=='text':
        if 'CMUSerif' in node.get('source_font',''):node['font_family']='Times New Roman'
        node['y']=max(0,node['y']-.15*node['font_size'])
        if 'Ital' in node.get('source_font',''):node['italic']=True
        node['label']=node['label'].replace('ﬁ','fi').replace('ﬂ','fl')
s['provenance']['text_editability']='Ordinary diagram labels and panel/callout prose are native typeable text. Mathematical glyph outlines, where present, remain editable point paths, not live equations.'
s['provenance']['font_substitutions']='CMU Serif and Nimbus Roman ordinary labels use Times New Roman or the editor Times-compatible fallback. Original geometry and math outlines retained.'
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(s['id'],sum(n['shape']=='text' for n in s['nodes']),'typeable text objects')
