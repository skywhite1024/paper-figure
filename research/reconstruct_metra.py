"""Reproduce the inspected source figure, retaining typeable ordinary labels."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/metra');a=p.parse_args()
c=json.loads((ROOT/'research/survey/metra-scalable-unsupervised-rl-with-metric-aware-abstraction-config.json').read_text());s=extract(a.pdf,c,a.out)
for node in s['nodes']:
    if node['shape']=='text':
        if 'CMUSerif' in node.get('source_font',''):node['font_family']='Times New Roman'
        node['y']=max(0,node['y']-.15*node['font_size'])
        if 'Ital' in node.get('source_font',''):node['italic']=True
        node['label']=node['label'].replace('ﬁ','fi').replace('ﬂ','fl')
# Merge source font spans that otherwise split a word or hyphenated phrase.
# The typeable Times substitute is slightly narrower than source CMU Serif.
# Flow the mixed-weight callout as three adjacent text boxes, centered on the
# original callout, rather than preserving artificial gaps between PDF spans.
byid={n['id']:n for n in s['nodes']}
near=byid['pdf-text-23-0'];last=byid['pdf-text-24-0']
near['label']='Temporally distant';near['width']=last['x']+last['width']-near['x']
bold=byid['pdf-text-19-0'];last=byid['pdf-text-21-0']
bold['label']='temporally spread-out';bold['width']=last['x']+last['width']-bold['x']
s['nodes']=[n for n in s['nodes'] if n['id'] not in ['pdf-text-24-0','pdf-text-20-0','pdf-text-21-0']]
import fitz
regular=fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf')
heavy=fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf')
parts=[byid['pdf-text-18-0'],bold,byid['pdf-text-22-0']]
center=(parts[0]['x']+parts[-1]['x']+parts[-1]['width'])/2
widths=[(heavy if n.get('bold') else regular).text_length(n['label'],fontsize=n['font_size']) for n in parts]
x=center-sum(widths)/2
for n,w in zip(parts,widths):n['x']=x;n['width']=w+.2;x+=w
first=byid['pdf-text-17-0'];first['label']=first['label'].strip();first['align']='center'
# Reviewed translucent thumbnail arrows contain overlapping subpaths. OOXML
# editors can apply even-odd fill to these compounds. Use explicit union
# outlines for the two straight arrows, and two ordinary curved-arrow pieces.
fixed=[]
for node in s['nodes']:
    if node['id']=='pdf-path-56':
        pts=[(15.2253112793,0),(0,7.6125183105),(15.2253112793,15.2252655029),(15.2253112793,10.150177002),(58.4745483398,10.150177002),(58.4745483398,5.0750427246),(15.2253112793,5.0750427246)]
        node['commands']=[{('moveTo' if i==0 else 'lineTo'):{'x':x,'y':y}} for i,(x,y) in enumerate(pts)]+[{'close':{}}]
    if node['id']=='pdf-path-60':
        pts=[(0,0),(43.2398071289,0),(43.2398071289,-5.0749969482),(58.4651184082,2.537612915),(43.2398071289,10.1502685547),(43.2398071289,5.0751800537),(0,5.075088501)]
        node['commands']=[{('moveTo' if i==0 else 'lineTo'):{'x':x,'y':y}} for i,(x,y) in enumerate(pts)]+[{'close':{}}]
    groups=[]
    if node['id']=='pdf-path-57':
        for cmd in node['commands']:
            if 'moveTo' in cmd:groups.append([])
            groups[-1].append(cmd)
    else:groups=[node.get('commands',[])]
    for i,commands in enumerate(groups):
        piece=dict(node)
        if len(groups)>1:piece['id']+=f'-part-{i}';piece['commands']=commands
        fixed.append(piece)
s['nodes']=fixed
s['provenance']['reviewed_arrow_repair']='Straight thumbnail arrows use explicit union outlines; curved thumbnail arrow uses separate source subpaths, avoiding editor even-odd cancellation at the shaft/head join.'
s['provenance']['text_editability']='Ordinary diagram labels and panel/callout prose are native typeable text. Mathematical glyph outlines, where present, remain editable point paths, not live equations.'
s['provenance']['font_substitutions']='CMU Serif and Nimbus Roman ordinary labels use Times New Roman or the editor Times-compatible fallback. Original geometry and math outlines retained.'
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(s['id'],sum(n['shape']=='text' for n in s['nodes']),'typeable text objects')
