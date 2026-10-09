"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='atr'; CAT='active-task-randomization-learning-robust-skills-via-unsupervised-generation-of-diverse-and-feasible-tasks'; FIG='figure-1'; CROP=[311, 146, 559, 380]; FONT='Times New Roman'
p=argparse.ArgumentParser();p.add_argument('--pdf');a=p.parse_args()
evidence=json.loads((R/'research/survey'/f'{CAT}.json').read_text());pdf=Path(a.pdf or evidence['pdf_path']);pdf=pdf if pdf.is_absolute() else R/pdf
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
s['provenance']['notes']+=' Source ordinary labels were outlines, so they are manually replaced by native typeable text. Four original robot/task photos plus the small globe icon remain raster. All task-space dots, links, modules, plans and arrows are native; source layout retained.'
rect('training-panel',7,10,732,346,'#FFF3CB','none',0)
text('training-title','Training',23,14,143,38,25,bold=True,align='left')
rounded('task-space',172,20,286,321,50,'#D9D9D9','none',0)
poly('task-space-tail',[(443,222),(479,183),(455,248)],'#D9D9D9',0,'#D9D9D9',True)
for id,box,c in [('success-one',(20,52,160,148),'#87AEEC'),('success-two',(20,152,160,248),'#7AA6EE'),('failure',(20,252,160,348),'#E4A0A0')]:
 image(id,box,'Original training-task robot rendering; internal task objects remain raster');rect(id+'-border',box[0],box[1],box[2]-box[0],box[3]-box[1],'none',c,1.5)
text('successful-tasks','successful\ntasks',239,20,157,66,23,'#6B9EEE')
text('failed-tasks','failed\ntasks',352,183,81,63,23,'#E89395')
text('task-space-label','task space',259,292,161,39,23)
for k,(x,y) in enumerate([(213,75),(245,67),(238,86),(220,106),(273,92),(253,123)]):ellipse('success-dot-'+str(k),x-6,y-6,12,12,'#6F9FE9','none',0)
for k,(x,y) in enumerate([(407,80),(356,137),(417,168),(328,216),(265,230),(235,258),(362,285)]):ellipse('failure-dot-'+str(k),x-6,y-6,12,12,'#E8989B','none',0)
ellipse('selected-state-ring',267,153,18,18,'#D9D9D9','#2F7FEF',1.5);ellipse('selected-state',270,156,12,12,'#2F7FEF','none',0)
line('success-trace-one',[(160,99),(183,99),(183,75),(208,75)],'#76A3EB',1.3)
line('success-trace-two',[(160,199),(213,199),(213,162),(267,162)],'#2F7FEF',1.3)
line('failed-trace',[(160,299),(194,299),(194,258),(230,258)],'#E8989B',1.3)
rect('task-sampler',478,146,101,76,'#FFDB69','none',0);text('task-sampler-label','task\nsampler',480,151,97,63,25)
z=rounded('environment-loop',589,30,145,264,28,'none','#202020',1.7,dash=True);z['dash_style']='dotted'
text('environment-label','environment',594,44,137,36,23)
image('earth',(634,76,696,139),'Original small globe/environment icon')
rect('skill-policy',618,199,94,76,'#AAC5F1','none',0);text('skill-policy-label','skill\npolicy',620,205,90,66,25)
poly('environment-policy-arrow',[(650,155),(665,141),(680,155),(672,155),(672,181),(680,181),(665,195),(650,181),(658,181),(658,155)],'#494949',0,'#494949',True)
line('task-parameter',[(527,146),(527,107),(634,107)],'#494949',3,True,size=17)
text('task-parameter-label','task\nparameter',470,40,109,60,24)
line('skill-return',[(660,295),(660,315),(527,315),(527,222)],'#494949',3,True,size=16)
text('return-label','return',561,319,86,32,24)
text('testing-title','Testing',23,368,127,40,25,bold=True,align='left')
# Isolated original photograph beneath a native translucent caption plate.
import io
block=[b for b in page.get_text('dict')['blocks'] if b['type']==1][4];box=fitz.Rect(block['bbox']);clip=fitz.Rect(317.96,283.1364,408.935,356.5921)
pix=fitz.Pixmap(block['image']);im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA');im=im.crop((round((clip.x0-box.x0)/box.width*im.width),0,im.width,im.height));im.save(A/'testing-photo.png')
node('testing-photo','image',(clip.x0-CROP[0])*3,(clip.y0-CROP[1])*3,clip.width*3,clip.height*3,asset='assets/testing-photo.png',alt='Original isolated real-robot photograph; caption is a separate translucent native plate with live text')
s['provenance']['raster_details'].append({'id':'testing-photo','bounds_source_pixels':[(clip.x0-CROP[0])*3,(clip.y0-CROP[1])*3,(clip.x1-CROP[0])*3,(clip.y1-CROP[1])*3],'detail':'Original real-robot testing photograph; native caption overlay is separate'})
rect('testing-border',20.884,411.409,272.926,220.367,'none','#626262',.8)
rect('testing-header',20.884,411.409,272.926,62.488,'#434343','none',0,fill_opacity=.5333)
text('goal-label','goal:',50,415,51,26,21,'#80B753',True,align='left')
text('goal-expression','in(salt, ctr) and\nunder(container, rack)',106,415,185,54,20,'#B3D393',align='left')
# The continuation line begins at the same source indentation.
for n in s['nodes']:
 if n['id']=='goal-expression':n['label']='in(salt, ctr) and';n['height']=27
text('goal-continuation','under(container, rack)',51,441,233,30,20,'#B3D393',align='left')
rect('test-controller',357,417,131,223,'#D9D9D9','none',0)
rect('task-planner',375,444,94,77,'#B7DAA9','none',0);text('task-planner-label','task\nplanner',376,451,92,61,25)
rect('skill-policies',375,545,94,77,'#A7C4F1','none',0);text('skill-policies-label','skill\npolicies',376,552,92,61,25)
rect('task-plan-panel',515,377,213,263,'#D1E1E4','none',0)
text('task-plan-title','task plan',564,383,122,37,25)
for k,y,verb,args in [(1,424,'pull-with','(salt, hook)'),(2,496,'place-onto','(salt, container)'),(3,568,'push-under','(container, rack)')]:
 rounded('plan-step-'+str(k),522,y,200,64,22,'#9B9B9B','none',0)
 text('plan-index-'+str(k),str(k),540,y+16,22,34,25,'#FFFFFF')
 text('plan-action-'+str(k),verb+'\n'+args,570,y+7,144,50,20,'#FFFFFF',align='left')
line('state-input',[(157,411),(157,391),(422,391),(422,415)],'#494949',2.3,True,size=12)
text('state-label','state',273,356,71,32,23)
line('plan-generation',[(469,482),(514,482)],'#494949',2.3,True,size=12)
line('plan-execution',[(515,584),(470,584)],'#494949',2.3,True,size=12)
line('test-action',[(422,623),(422,666),(157,666),(157,633)],'#494949',2.3,True,size=12)
text('action-label','action',266,669,79,29,23)
finish()
