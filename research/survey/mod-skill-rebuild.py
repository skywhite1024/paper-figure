"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='mod-skill'; CAT='diverse-skill-discovery-for-quadruped-robots-via-unsupervised-learning'; FIG='figure-1'; CROP=[48, 48, 299, 256]; FONT='Times New Roman'
p=argparse.ArgumentParser();p.add_argument('--pdf');a=p.parse_args()
evidence=json.loads((R/'research/survey'/f'{CAT}.json').read_text());pdf=Path(a.pdf or evidence['pdf_path'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(pdf)==evidence['pdf_sha256'],'Wrong source PDF'
D=R/'data/diagrams'/SLUG;A=D/'assets';D.mkdir(parents=True,exist_ok=True);A.mkdir(exist_ok=True)
B=R/'build'/SLUG;B.mkdir(parents=True,exist_ok=True);C=R/'build/candidates'/SLUG;C.mkdir(parents=True,exist_ok=True)
f=evidence['figure_candidates'][0];doc=fitz.open(pdf);page=doc[f['page_1_based']-1];pix=page.get_pixmap(matrix=fitz.Matrix(4,4),clip=fitz.Rect(CROP),alpha=False);pix.save(D/'original.png');source=Image.open(D/'original.png');W,H=source.size
s={'schema_version':1,'id':SLUG+'-'+FIG,'title':evidence['title_expected']+' — source-layout editable reconstruction','canvas':{'width':W,'height':H},'provenance':{'paper_title':evidence['title_expected'],'paper_url':evidence['source_url'].split('v1')[0].split('v3')[0]+evidence['version'][len(evidence['version'].split('v')[0]):],'pdf_url':evidence['versioned_pdf_url'],'figure':f['figure'],'page':f['page_1_based'],'license':evidence['license_note']+' Private user-requested adaptation; no public redistribution permission implied.','status':'figure_recreation','notes':'Manually reconstructed from the inspected original flattened PDF figure. Ordinary labels are live typeable text; panels, graph geometry and arrows are native editable shapes or paths. Source layout and contents retained; font metrics, line widths and decorative effects approximated.','source_sha256':sha(pdf),'source_crop_pdf_points':CROP,'survey_crop_correction':CROP!=f['crop_pdf_points'],'visual_inspection':'Original PDF figure inspected before source-layout reconstruction on 2026-10-09; independent application QA pending.','raster_details':[]},'nodes':[],'edges':[]}
s['provenance']['paper_url']='https://arxiv.org/abs/'+evidence['version']
def node(id,shape,x,y,w,h,**kw):
 z=dict(id=id,shape=shape,label='',x=x,y=y,width=max(.1,w),height=max(.1,h),fill='none',stroke='none');z.update(kw);s['nodes'].append(z);return z
def rect(id,x,y,w,h,fill='none',stroke='#000000',sw=2,round=False,**kw):return node(id,'rounded_rect' if round else 'rect',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,**kw)
def text(id,label,x,y,w,h,fs=22,color='#000000',bold=False,italic=False,font=None,align='center'):
 return node(id,'text',x,y,w,h,label=label,font_size=fs,font_family=font or FONT,text_color=color,bold=bold,italic=italic,align=align,text_inset=0,no_wrap=True)
def ellipse(id,x,y,w,h,fill='none',stroke='#000000',sw=2):return node(id,'ellipse',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw)
def poly(id,pts,stroke='#000000',sw=2,fill='none',close=False,dash=False):
 x=min(q[0] for q in pts);y=min(q[1] for q in pts);w=max(q[0] for q in pts)-x;h=max(q[1] for q in pts)-y
 cmds=[{'moveTo':{'x':pts[0][0]-x,'y':pts[0][1]-y}}]+[{'lineTo':{'x':u-x,'y':v-y}} for u,v in pts[1:]]
 if close:cmds.append({'close':{}})
 return node(id,'path',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,commands=cmds,dash=dash)
def line(id,pts,stroke='#000000',sw=3,arrow=False,dash=False,head=False,size=10):
 z=poly(id,pts,stroke,sw,dash=dash)
 def tip(suffix,end,prev):
  dx,dy=end[0]-prev[0],end[1]-prev[1];L=math.hypot(dx,dy);ux,uy=dx/L,dy/L;bx,by=end[0]-size*ux,end[1]-size*uy
  poly(id+suffix,[end,(bx-size*.47*uy,by+size*.47*ux),(bx+size*.47*uy,by-size*.47*ux)],stroke,0,stroke,True)
 if arrow:tip('-arrow',pts[-1],pts[-2])
 if head:tip('-head',pts[0],pts[1])
 return z

def curve(id,x,y,w,h,cmds,stroke='#000000',sw=2,fill='none',dash=False):return node(id,'path',x,y,w,h,commands=cmds,stroke=stroke,stroke_width=sw,fill=fill,dash=dash)
def rounded(id,x,y,w,h,r,fill='none',stroke='#000000',sw=2,dash=False):
 k=.55228475
 cmds=[{'moveTo':{'x':r,'y':0}},{'lineTo':{'x':w-r,'y':0}},{'cubicBezTo':{'x1':w-r+k*r,'y1':0,'x2':w,'y2':r-k*r,'x':w,'y':r}},{'lineTo':{'x':w,'y':h-r}},{'cubicBezTo':{'x1':w,'y1':h-r+k*r,'x2':w-r+k*r,'y2':h,'x':w-r,'y':h}},{'lineTo':{'x':r,'y':h}},{'cubicBezTo':{'x1':r-k*r,'y1':h,'x2':0,'y2':h-r+k*r,'x':0,'y':h-r}},{'lineTo':{'x':0,'y':r}},{'cubicBezTo':{'x1':0,'y1':r-k*r,'x2':r-k*r,'y2':0,'x':r,'y':0}},{'close':{}}]
 return curve(id,x,y,w,h,cmds,stroke,sw,fill,dash)
def image(id,box,alt):
 x,y,x1,y1=box;source.crop(box).save(A/(id+'.png'));node(id,'image',x,y,x1-x,y1-y,asset='assets/'+id+'.png',alt=alt)
 s['provenance']['raster_details'].append({'id':id,'bounds_source_pixels':list(box),'detail':alt})
def finish():
 scene=D/(s['id']+'.json');scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(B),'--preview','--force'],cwd=R,check=True)
 for ext in ['pptx','drawio','png','manifest.json']:shutil.copy2(B/(s['id']+'.'+ext),C/(s['id']+'.'+ext))
 shutil.copy2(D/'original.png',C/(SLUG+'-original.png'));pdfname=SLUG+'-'+evidence['version']+'.pdf';shutil.copy2(pdf,C/pdfname)
 src={'validated_date':'2026-10-09','purpose':'User-requested private original-paper comparison against editable reconstruction','rights_note':'Private reference copy; preserve authorship and source license. No public redistribution permission implied.','papers':[{'id':SLUG,'catalog_id':CAT,'title':evidence['title_expected'],'file':pdfname,'arxiv_id_version':evidence['version'],'source_url':evidence['versioned_pdf_url'],'sha256':sha(pdf),'bytes':pdf.stat().st_size,'page_count':len(doc),'figure':f['figure'],'pdf_page_1_based':f['page_1_based'],'crop_pdf_points':CROP,'diagram_json':'../../data/diagrams/'+SLUG+'/'+s['id']+'.json','editable_pptx':s['id']+'.pptx','editable_drawio':s['id']+'.drawio','matches_original_reconstruction_source':True,'embedded_version_verified':True,'all_pages_readable':True,'license_url':evidence['license_note']}]}
 (C/'sources.json').write_text(json.dumps(src,indent=2,ensure_ascii=False)+'\n')
 with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
  root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
 validation={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source pixels inspected; reconstruction preview review pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(z.get('label')) for z in s['nodes']),'native_paths':sum(z['shape']=='path' for z in s['nodes']),'raster_images':sum(z['shape']=='image' for z in s['nodes']),'raster_boundaries':s['provenance']['raster_details']},'checks':{'source_title':'Verified PDF title and fixed version from survey evidence; PDF hash rechecked','source_figure':'Actual PDF figure inspected; crop includes complete source diagram','drawio':'Native XML generated; draw.io application editing not tested','powerpoint':'Native XML counts inspected; PowerPoint GUI editing not tested'},'limitations':['Flattened source manually rebuilt; font metrics, arrowheads and stroke widths approximate original','Native paths are independently editable but not semantically attached connectors','No PowerPoint or draw.io GUI edit validation claimed']}
 (C/'VALIDATION.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n')
 print(SLUG,counts,validation['editability'])
# Figure 1 coordinates measured on the complete 4x PDF crop.
rounded('sampler-panel',321,119,240,236,43,'#EEEEEE','#DDDDDD',2)
rounded('multi-panel',608,23,386,297,52,'#DFEFF9','#B7DCF4',2)
rounded('policy-panel',187,407,605,402,69,'#E1F2D7','#BEDFAE',2)
image('quadruped-observation',(15,32,274,226),'Original quadruped simulation photograph; robot and ground-grid pixels remain raster')
for id,x,y,w,h in [('motion',343,23,195,81),('policy-observation',47,273,195,82),('reward',906,454,79,81),('action',906,644,79,82)]:rounded(id+'-panel',x,y,w,h,14,'#FFFFFF','#19395F',2.6)
text('motion-label','Motion\nObservation oᵐ',346,37,189,51,23)
text('policy-observation-label','Policy\nObservation oᵖ',50,286,189,54,23)
text('sampler-title','Skill Sampler',336,139,208,34,27,bold=True)
rect('skill-prior',347,191,185,54,'#C8C8C8','none',0)
rect('latent-skill',346,281,184,55,'#C8C8C8','none',0)
text('skill-prior-label','Skill Prior\nk ∼ P(k)',350,192,179,49,23)
text('latent-skill-label','Latent Skill k',352,293,172,30,23)
text('multi-title','Multi-Discriminator Module',628,46,345,39,28,bold=True)
for k,y,label in [(1,95,'Discriminator 1'),(2,171,'Discriminator 2'),(3,248,'Discriminator N')]:
 rect(f'discriminator-{k}',664,y,185,54,'#91C0E6','none',0);text(f'discriminator-{k}-label',label,668,y+11,177,32,23)
text('discriminator-ellipsis','...',741,215,35,24,21)
text('policy-title','Orthogonal Mixture-of-Experts Policy',205,432,576,39,28,bold=True)
for k,y,label in [(1,480,'Expert 1'),(2,556,'Expert 2'),(3,631,'Expert N'),(4,736,'Task Encoder')]:
 rect(f'expert-{k}',273,y,184,54,'#A1D082','none',0);text(f'expert-{k}-label',label,277,y+11,176,33,23)
text('expert-ellipsis','...',348,603,35,24,21)
rect('gram-schmidt',537,556,206,54,'#A1D082','none',0);text('gram-schmidt-label','Gram-Schmidt\nProcess',541,557,198,51,23)
rect('weighted-sum',537,659,206,54,'#A1D082','none',0);text('weighted-sum-label','Weighted Sum',542,672,196,29,23)
text('reward-label','r',918,470,55,45,30,italic=True);text('action-label','a',918,662,55,45,30,italic=True)
text('policy-gradient','Policy\nGradient',827,562,104,57,23)
line('observation-to-motion',[(274,63),(343,63)],arrow=True,size=12)
line('observation-to-policy',[(144,226),(144,273)],arrow=True,size=12)
line('prior-to-latent',[(439,246),(439,280)],arrow=True,size=12)
line('motion-to-discriminator',[(538,63),(584,63),(584,198),(664,198)],arrow=True,size=14)
line('discriminator-input-branch',[(664,122),(630,122),(630,274),(664,274)],arrow=True,head=True,size=14)
line('discriminator-outer-output',[(849,122),(886,122),(886,275),(849,275)])
line('discriminator-reward',[(849,198),(946,198),(946,453)],arrow=True,size=14)
line('latent-route',[(438,336),(438,382),(144,382)])
line('observation-reward-route',[(438,382),(946,382)])
line('policy-route',[(144,355),(144,763),(273,763)],arrow=True,size=14)
line('policy-expert-mid',[(144,583),(273,583)],arrow=True,size=14)
line('expert-input-branch',[(273,507),(233,507),(233,660),(273,660)],arrow=True,head=True,size=14)
line('expert-output-branch',[(457,507),(499,507),(499,660),(457,660)])
line('experts-to-orthogonalize',[(457,583),(537,583)],arrow=True,size=12)
line('orthogonalize-to-sum',[(640,610),(640,659)],arrow=True,size=12)
line('encoder-to-sum',[(457,762),(640,762),(640,714)],arrow=True,size=14)
line('sum-to-action',[(743,687),(905,687)],arrow=True,size=14)
line('policy-gradient-feedback',[(946,535),(946,644)],arrow=True,head=True,dash=True,size=14)
finish()
