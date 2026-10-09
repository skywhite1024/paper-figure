"""Paper-specific reconstruction of the inspected original PDF figure."""
import json,hashlib,subprocess,sys,zipfile,xml.etree.ElementTree as ET,fitz
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from paper_figure.pdf_extract import extract
from research.prepare_candidate import prepare
SLUG='video2policy';CAT='video2policy-scaling-up-manipulation-tasks-in-simulation-through-internet-videos'
evidence_path=R/'research/survey'/f'{CAT}.json';ev=json.loads(evidence_path.read_text());pdf=Path(ev['pdf_path']);pdf=pdf if pdf.is_absolute() else R/pdf
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(pdf)==ev['pdf_sha256']
D=R/'data/diagrams'/SLUG;B=R/'build'/SLUG;C=R/'build/candidates'/SLUG;cfg=json.loads((R/'research/survey'/f'{SLUG}-config.json').read_text())
s=extract(pdf,cfg,D);scene=D/(s['id']+'.json')
# Preserve source rotations as native live text, including the curved-label character placements.
import math
traces=fitz.open(pdf)[cfg['page']-1].get_texttrace()
for n in s['nodes']:
 if n['shape']!='text' or not n['id'].startswith('pdf-text-'):continue
 idx=int(n['id'].split('-')[2]);span=traces[idx];dx,dy=span.get('dir',(1,0))
 if abs(dy)<.0001 and dx>0:continue
 cx=n['x']+n['width']/2;cy=n['y']+n['height']/2
 font=fitz.Font('tiro' if n['font_family']=='Times New Roman' else 'helv')
 width=max(1,font.text_length(n['label'],fontsize=n['font_size']));height=n['font_size']
 n.update(x=cx-width/2,y=cy-height/2,width=width,height=height,rotation=math.degrees(math.atan2(dy,dx)))
s['provenance']['notes']+=' Reviewed source text rotation preserved as native rotated text; curved wording remains separate typeable characters at source positions.'

# PAPER_SPECIFIC_POSTPROCESS
scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(B),'--preview','--force'],cwd=R,check=True)
prepare(SLUG,evidence_path,scene,B,D/(s['id']+'-original.png'))
with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
validation={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source inspected; generated preview comparison pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(n.get('label')) for n in s['nodes']),'native_paths':sum(n['shape']=='path' for n in s['nodes']),'raster_images':sum(n['shape']=='image' for n in s['nodes']),'raster_boundaries':[{'id':n['id'],'bounds_canvas':[n[k] for k in ['x','y','width','height']],'detail':n['alt']} for n in s['nodes'] if n['shape']=='image']},'limitations':['Source native geometry retained; fonts and dash/arrow rendering can vary','Native paths are editable but lack automatic semantic attachment','No PowerPoint or draw.io GUI editing validation claimed']}
(C/'VALIDATION.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n');print(SLUG,validation['editability'])
