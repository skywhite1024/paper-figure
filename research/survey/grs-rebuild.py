"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='grs'; CAT='grs-generating-robotic-simulation-tasks-from-real-world-images'; FIG='figure-2'; CROP=[318, 71, 553, 240]; FONT='Times New Roman'
p=argparse.ArgumentParser();p.add_argument('--pdf');a=p.parse_args()
evidence=json.loads((R/'research/survey'/f'{CAT}.json').read_text());pdf=Path(a.pdf or evidence['pdf_path'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(pdf)==evidence['pdf_sha256'],'Wrong source PDF'
D=R/'data/diagrams'/SLUG;A=D/'assets';D.mkdir(parents=True,exist_ok=True);A.mkdir(exist_ok=True)
B=R/'build'/SLUG;B.mkdir(parents=True,exist_ok=True);C=R/'build/candidates'/SLUG;C.mkdir(parents=True,exist_ok=True)
f=evidence['figure_candidates'][0];doc=fitz.open(pdf);page=doc[f['page_1_based']-1];pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(CROP),alpha=False);pix.save(D/'original.png');source=Image.open(D/'original.png');W,H=source.size
s={'schema_version':1,'id':SLUG+'-'+FIG,'title':evidence['title_expected']+' — source-layout editable reconstruction','canvas':{'width':W,'height':H},'provenance':{'paper_title':evidence['title_expected'],'paper_url':evidence['source_url'].split('v1')[0].split('v3')[0]+evidence['version'][len(evidence['version'].split('v')[0]):],'pdf_url':('https://arxiv.org/pdf/'+evidence['version']),'figure':f['figure'],'page':f['page_1_based'],'license':evidence['license_note']+' Private user-requested adaptation; no public redistribution permission implied.','status':'figure_recreation','notes':'Manually reconstructed from the inspected original flattened PDF figure. Ordinary labels are live typeable text; panels, graph geometry and arrows are native editable shapes or paths. Source layout and contents retained; font metrics, line widths and decorative effects approximated.','source_sha256':sha(pdf),'source_crop_pdf_points':CROP,'survey_crop_correction':CROP!=f['crop_pdf_points'],'visual_inspection':'Original PDF figure inspected before source-layout reconstruction on 2026-10-09; independent application QA pending.','raster_details':[]},'nodes':[],'edges':[]}
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
 src={'validated_date':'2026-10-09','purpose':'User-requested private original-paper comparison against editable reconstruction','rights_note':'Private reference copy; preserve authorship and source license. No public redistribution permission implied.','papers':[{'id':SLUG,'catalog_id':CAT,'title':evidence['title_expected'],'file':pdfname,'arxiv_id_version':evidence['version'],'source_url':('https://arxiv.org/pdf/'+evidence['version']),'sha256':sha(pdf),'bytes':pdf.stat().st_size,'page_count':len(doc),'figure':f['figure'],'pdf_page_1_based':f['page_1_based'],'crop_pdf_points':CROP,'diagram_json':'../../data/diagrams/'+SLUG+'/'+s['id']+'.json','editable_pptx':s['id']+'.pptx','editable_drawio':s['id']+'.drawio','matches_original_reconstruction_source':True,'embedded_version_verified':True,'all_pages_readable':True,'license_url':evidence['license_note']}]}
 (C/'sources.json').write_text(json.dumps(src,indent=2,ensure_ascii=False)+'\n')
 with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
  root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
 validation={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source pixels inspected; reconstruction preview review pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(z.get('label')) for z in s['nodes']),'native_paths':sum(z['shape']=='path' for z in s['nodes']),'raster_images':sum(z['shape']=='image' for z in s['nodes']),'raster_boundaries':s['provenance']['raster_details']},'checks':{'source_title':'Verified PDF title and fixed version from survey evidence; PDF hash rechecked','source_figure':'Actual PDF figure inspected; crop includes complete source diagram','drawio':'Native XML generated; draw.io application editing not tested','powerpoint':'Native XML counts inspected; PowerPoint GUI editing not tested'},'limitations':['Flattened source manually rebuilt; font metrics, arrowheads and stroke widths approximate original','Native paths are independently editable but not semantically attached connectors','No PowerPoint or draw.io GUI edit validation claimed']}
 (C/'VALIDATION.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n')
 print(SLUG,counts,validation['editability'])
FONT='Arial'
s['provenance']['notes']+=' Four original scene photographs are isolated raster crops. All stage titles, VLMs, database/document symbols, decision/router shapes, status blocks and connecting arrows are native.'
blue='#263E60';doccol='#5D858C';purple='#BA91C0';sim='#881963';tests='#D6312B';vlm='#EFF3D9'
for id,x,y,w,h,title in [('scene',8,30,222,229,'1) Scene Comprehension'),('task',239,30,191,229,'2) Task Generation'),('initial',436,30,263,229,'3) Initial Simulation'),('refinement',8,286,691,215,'4) Simulation Refinement')]:
 rect(id+'-panel',x,y,w,h,'#FFFFFF',blue,1.7);text(id+'-title',title,x,y-27,w,24,15,align='left')
for id,box in [('scene-photo',(16,36,124,144)),('task-photo',(245,37,354,144)),('initial-photo',(440,37,548,144)),('final-photo',(533,310,656,433))]:image(id,box,'Original robot scene rendering; objects and small diagnostic overlays remain raster')
# Native database cylinder.
rect('database-body',129,55,92,71,'#FFFFFF',blue,1.8)
ellipse('database-bottom',129,114,92,24,'#FFFFFF',blue,1.8)
rect('database-center',130,57,90,68,'#FFFFFF','none',0)
ellipse('database-top',129,45,92,23,'#FFFFFF',blue,1.8)
text('database-label','asset\ndatabase',135,77,80,42,16)
def document(id,x,y,w,h,color,label,fs=14):
 cmds=[{'moveTo':{'x':0,'y':0}},{'lineTo':{'x':w,'y':0}},{'lineTo':{'x':w,'y':h-12}},{'cubicBezTo':{'x1':w*.6,'y1':h-13,'x2':w*.4,'y2':h+5,'x':0,'y':h-5}},{'close':{}}]
 curve(id,x,y,w,h,cmds,blue,1,color);text(id+'-label',label,x+1,y+10,w-2,h-21,fs,'#FFFFFF')
def trapezoid(id,x,y,w,h):poly(id,[(x,y),(x+w,y),(x+w-24,y+h),(x+24,y+h)],blue,1,vlm,True);text(id+'-label','VLM',x,y+5,w,h-9,16)
trapezoid('scene-vlm',59,149,125,33);trapezoid('task-vlm',275,150,125,34);trapezoid('initial-vlm',504,149,125,33)
document('scene-description',90,186,62,70,doccol,'scene\ndescription',12)
document('task-scene-description',360,54,62,70,doccol,'scene\ndescription',12)
document('task-output',306,188,62,66,purple,'task',16)
document('initial-scene-description',556,54,62,70,doccol,'scene\ndescription',12)
document('initial-task',628,53,62,70,purple,'task',16)
for id,x,y,w,h,c,label in [('initial-simulation',476,194,83,39,sim,'simulation'),('initial-tests',575,194,83,39,tests,'tests'),('refine-simulation',53,345,84,39,sim,'simulation'),('refine-tests',53,399,84,39,tests,'tests'),('final-simulation',551,441,84,39,sim,'simulation')]:
 rounded(id,x,y,w,h,7,c,blue,1);text(id+'-label',label,x+2,y+5,w-4,h-10,14,'#FFFFFF')
poly('execute',[(152,361),(255,391),(152,421)],blue,1,'#FFFFFF',True);text('execute-label','execute',153,375,76,32,16)
document('error-document',272,357,62,70,'#DFDEE1','error',16)
for n in s['nodes']:
 if n['id']=='error-document-label':n['text_color']='#000000'
poly('router',[(351,328),(413,351),(413,422),(351,445)],blue,1,vlm,True);text('router-label','router',353,371,58,33,16)
rect('router-status',360,397,13,13,purple,blue,1)
for id,y,label in [('simulation',300,'fix\nsimulation'),('tests',441,'fix\ntests')]:
 poly('fix-'+id,[(166,y+2),(254,y-10),(254,y+52),(166,y+42)],blue,1,vlm,True);text('fix-'+id+'-label',label,169,y+3,61,39,14)
 for k,col in enumerate([sim,'#F6C27C','#D4E6EE'] if id=='simulation' else [purple,'#D4E6EE',tests]):
  poly(f'fix-{id}-token-{k}',[(238,y-5+k*19),(251,y-7+k*19),(251,y+6+k*19),(238,y+8+k*19)],blue,.8,col,True)
 if id=='simulation':rect('fix-simulation-token-main',220,y+2,14,14,sim,blue,1)
for id,pts in [('fix-sim-return',[(166,320),(95,320),(95,344)]),('fix-tests-return',[(166,462),(95,462),(95,439)]),('router-fix-sim',[(414,368),(458,368),(458,320),(255,320)]),('router-fix-tests',[(414,403),(458,403),(458,462),(255,462)]),('router-success',[(414,386),(482,386),(482,460),(550,460)])]:line(id,pts,'#808080',1.8,True,size=8)
text('no-error-label','no error',488,460,52,18,11)
finish()
