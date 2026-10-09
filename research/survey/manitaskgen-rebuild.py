"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='manitaskgen'; CAT='manitaskgen-a-comprehensive-task-generator-for-benchmarking-and-improving-vision-language-agents-on-embodied-decision-making'; FIG='figure-1'; CROP=[107, 71, 506, 182]; FONT='Times New Roman'
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
s['provenance']['notes']+=' Five manipulation benchmark snapshots, the scene photograph, gear brand icon and five small robot/notepad illustrations remain isolated raster crops. All task cards, task examples, labels, flow arrows, status legend, improvement-loop geometry and deployment trend are native.'
blue='#709FC8';orange='#C58E6F';green='#648F56';darkgreen='#376934'
image('scene-photo',(6,22,159,118),'Original furnished-scene overhead image')
image('gear-logo',(264,36,327,96),'Original ManiTaskGen gear mark; its internal artwork remains raster')
text('scene-info','Scene Info',41,116,89,18,14)
text('brand-left','ManiTask',215,102,118,31,25,bold=True,font='Courier New')
text('brand-right','Gen',332,102,50,31,25,'#447C33',True,font='Courier New')
for k,y in enumerate([69,76,83]):line('scene-to-generator-'+str(k),[(168,y),(251,y)],'#555555',1.6,True,size=7)
for id,pts,c in [('generator-benchmark',[(334,69),(428,69)],blue),('generator-improve',[(334,82),(416,82),(416,178),(428,178)],orange)]:line(id,pts,c,1.5,True,size=8)
line('generator-tasks',[(296,129),(296,157),(120,157),(120,186)],green,2,True,size=6)
line('generator-process',[(296,157),(324,157),(324,186)],green,2,True,size=6)
def taskcard(id,x,y,w,h,col):
 cmds=[{'moveTo':{'x':0,'y':0}},{'lineTo':{'x':w,'y':0}},{'lineTo':{'x':w,'y':h-19}},{'cubicBezTo':{'x1':w*.66,'y1':h-21,'x2':w*.42,'y2':h+11,'x':0,'y':h-2}},{'close':{}}]
 curve(id,x,y,w,h,cmds,col,3,'#F2F8EA')
for id,x,col in [('outcome',7,'#6EA446'),('process',211,darkgreen)]:
 for j,dx,dy in [(2,27,-21),(1,13,-10),(0,0,0)]:taskcard(f'{id}-card-{j}',x+dx,207+dy,172,101,col)
text('outcome-task-id','Task_123:',20,217,77,22,16,bold=True,font='Times New Roman',align='left')
text('outcome-task-start','Clean up',97,217,74,22,16,italic=True,font='Times New Roman',align='left')
text('outcome-task-body','the second layer from\nthe top of book_shelf.',20,239,158,45,16,italic=True,font='Times New Roman',align='left')
text('process-task-id','Task_456:',221,214,77,22,16,bold=True,font='Times New Roman',align='left')
text('process-task-start','Move',297,214,68,22,16,italic=True,font='Times New Roman',align='left')
text('process-task-body','remote_control from\ntv_stand to left part of\nthe tabletop.',221,235,160,61,16,italic=True,font='Times New Roman',align='left')
text('outcome-label','Outcome-based Tasks',30,309,156,22,14)
text('process-label','Process-based Tasks',234,309,154,22,14)
rounded('benchmark-heading-bar',429,21,760,40,6,'#DFEBF6','none',0)
text('benchmark-heading','Agent Benchmark',437,24,187,31,20,'#494949',True,align='left')
for id,x,c,sign,label,w in [('success',644,'#507F37','✓','SUCCESS',82),('failure',754,'#B72F12','×','FAIL',53),('timeout',839,'#000000','−','TIMEOUT',80)]:
 ellipse(id+'-icon',x-12,28,24,24,c,'none',0);text(id+'-sign',sign,x-10,28,20,24,20,'#FFFFFF');text(id+'-label',label,x+15,31,w,19,13,c,True,font='Times New Roman',align='left')
for k,h in enumerate([8,14,20,24]):rect('points-bar-'+str(k),946+k*5,51-h,3,h,'#8040AD','none',0)
text('points-label','INTERMEDIATE POINTS',974,31,198,21,13,'#8040AD',True,font='Times New Roman',align='left')
for id,x,w,heading in [('navigate',429,262,'NAVIGATE'),('grasp',695,246,'GRASP'),('place',945,244,'PLACE')]:
 rect(id+'-frame',x,66,w,97,'#FFFFFF',blue,1.2);rect(id+'-heading-back',x+1,67,w-2,16,'#DFEBF6','none',0);text(id+'-heading',heading,x,65,w,21,14,'#4B4B4B',True)
for id,box in [('sofa',(548,94,679,156)),('grasp-start',(699,94,798,156)),('grasp-end',(839,94,938,156)),('place-start',(949,94,1046,156)),('place-end',(1088,94,1185,156))]:image(id,box,'Original robot task benchmark snapshot; tiny numbered segmentation overlays remain raster')
for id,box in [('benchmark-robot',(434,94,476,151)),('reflection-robot',(434,250,476,309)),('memory-notepad',(808,253,845,300)),('deployment-robot',(956,245,999,309)),('deployment-notepad',(1027,253,1063,302))]:image(id,box,'Original small robot/notepad icon; internal line-art pixels remain raster')
for id,label,x,w in [('navigation','go_to_sofa',479,64),('grasp','pick_2',798,38),('place','place_7',1047,40)]:
 text(id+'-action',label,x,107,w,21,14,italic=True,font='Times New Roman');line(id+'-action-arrow',[(x,126),(x+w,126)],blue,1.5,True,size=6)
rounded('improvement-heading-bar',429,174,760,40,6,'#F8E6DA','none',0)
text('improvement-heading','Agent Improvement',438,178,268,30,20,'#494949',True,align='left')
for id,x,w,lab in [('trials',429,512,'Trials and Reflections'),('deployment',945,244,'Deployment')]:
 rect(id+'-frame',x,219,w,107,'#FFFFFF',orange,1.2);rect(id+'-heading-back',x+1,220,w-2,14,'#F8E6DA','none',0);text(id+'-heading',lab,x,216,w,22,14,'#4B4B4B',True)
for id,x,y,w,h,c,label in [('trajectory',521,238,96,25,'#D5E5F5','Trajectory'),('evaluator',521,294,96,25,'#CFE7BF','Evaluator'),('reflection',629,266,124,25,'#F3D7C6','Self-Reflection')]:
 rounded(id,x,y,w,h,2,c,'#737373',1);text(id+'-label',label,x+1,y+2,w-2,h-4,14,'#464646',True)
line('trajectory-evaluator',[(569,263),(569,294)],'#606060',1.4,True,size=7)
curve('evaluator-reflection',617,290,74,17,[{'moveTo':{'x':0,'y':17}},{'cubicBezTo':{'x1':29,'y1':17,'x2':64,'y2':15,'x':74,'y':0}}],'#606060',1.5)
poly('evaluator-reflection-tip',[(690,290),(683,291),(689,298)],'#606060',0,'#606060',True)
curve('reflection-trajectory',617,250,75,17,[{'moveTo':{'x':75,'y':17}},{'cubicBezTo':{'x1':69,'y1':4,'x2':26,'y2':0,'x':0,'y':0}}],'#606060',1.5)
poly('reflection-trajectory-tip',[(617,250),(624,246),(624,254)],'#606060',0,'#606060',True)
curve('robot-to-trajectory',474,247,46,33,[{'moveTo':{'x':0,'y':33}},{'cubicBezTo':{'x1':0,'y1':9,'x2':26,'y2':3,'x':46,'y':0}}],blue,1.1,dash=True)
line('reflection-memory',[(758,280),(803,280)],'#D6A88B',1.2,True,True,True,size=6)
text('memory-label','Long-term\nMemory',848,261,86,36,14,align='left')
ellipse('deployment-plus-circle',1004,271,15,15,'#000000','none',0);text('deployment-plus','+',1006,270,12,16,14,'#FFFFFF')
text('deployment-equals','=',1066,263,19,29,23,bold=True)
line('deployment-x',[(1103,302),(1179,302)],'#54852C',1.1,True,size=6)
line('deployment-y',[(1103,302),(1103,247)],'#54852C',1.1,True,size=6)
curve('deployment-success',1112,265,57,31,[{'moveTo':{'x':0,'y':31}},{'cubicBezTo':{'x1':12,'y1':26,'x2':17,'y2':25,'x':26,'y':17}},{'cubicBezTo':{'x1':33,'y1':6,'x2':43,'y2':3,'x':57,'y':0}}],'#B6DF9A',2)
z=text('success-axis-label','Success',1076,266,40,14,11);z['rotation']=-90
text('trials-axis-label','Trials',1124,300,34,19,11)
late_ids={'reflection-robot','memory-notepad','deployment-robot','deployment-notepad'}
s['nodes']=[n for n in s['nodes'] if n['id'] not in late_ids]+[n for n in s['nodes'] if n['id'] in late_ids]
finish()
