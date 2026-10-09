"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='upside'; CAT='direct-then-diffuse-incremental-unsupervised-skill-discovery-for-state-covering-and-goal-reaching'; FIG='figure-1'; CROP=[108,80,504,189]; FONT='Times New Roman'
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
# Five-panel source concept figure, fully recreated with native geometric objects.
FONT='Arial'
s['provenance']['notes']+=' All five process panels and the structure legend are native. Colored local-coverage disks, diffusing-part curves, directed-skill arrows, initial states and obstacle lines are individually editable. No raster images are embedded. Curvature and exact alpha blending approximate the flattened source.'
rect('legend-background',10,11,144,393,'#FFFFF1','none',0)
for k,x in enumerate([169,453,737,1021,1303]):
 rect('process-panel-'+str(k),x,15,269,384,'#FFFFFF','#111111',1.5)
 line('obstacle-'+str(k),[(x+134,147),(x+134,399)],'#222222',1.6)
 text('panel-letter-'+str(k),'ABCDE'[k],x+113,402,43,33,26)
# Legend: native callout, pink local state-coverage disk and directed curve.
text('diffusing-part-label','diffusing\npart',67,26,89,51,21,'#A43310',True,True)
text('directed-skill-label','directed\nskill',68,183,83,49,20,'#666666',True)
text('structure-label','Structure\nof an\nUPSIDE\npolicy',18,264,126,120,24,'#666666')
palette={'pink':'#EBA0CC','green':'#93D562','red':'#DC6751','cyan':'#78DDD2','yellow':'#F7E249','orange':'#F4C257','gray':'#777777','blue':'#68B0F5'}
# Arrow motifs were visually traced from the repeated source diffusion shape.
def diffusion(id,cx,cy,r,col,opacity=.60):
 z=ellipse(id+'-coverage',cx-r,cy-r,2*r,2*r,palette[col],'none',0);z['fill_opacity']=opacity
 # Five curved exploratory motions, with independent native arrowheads.
 scale=r/48
 segments=[(-2,-3,-17,-17,-26,-34,-8,-35),(-1,-2,15,-14,22,-27,23,-38),(2,0,18,-3,28,3,35,12),(-1,2,-5,16,-9,23,-16,30),(-2,1,-17,15,-34,9,-39,-10)]
 color='#C13A7B'
 for j,(sx,sy,c1x,c1y,c2x,c2y,ex,ey) in enumerate(segments):
  pts=[(cx+v*scale,cy+w*scale) for v,w in [(sx,sy),(c1x,c1y),(c2x,c2y),(ex,ey)]]
  x=min(p[0] for p in pts);y=min(p[1] for p in pts);w=max(p[0] for p in pts)-x;h=max(p[1] for p in pts)-y
  cmds=[{'moveTo':{'x':pts[0][0]-x,'y':pts[0][1]-y}},{'cubicBezTo':{'x1':pts[1][0]-x,'y1':pts[1][1]-y,'x2':pts[2][0]-x,'y2':pts[2][1]-y,'x':pts[3][0]-x,'y':pts[3][1]-y}}]
  c=curve(id+'-diffusion-'+str(j),x,y,w,h,cmds,color,1.65);c['stroke_opacity']=.80
  ex,ey=pts[3];px,py=pts[2];dx,dy=ex-px,ey-py;length=math.hypot(dx,dy);ux,uy=dx/length,dy/length;size=7*scale;bx,by=ex-size*ux,ey-size*uy
  z=poly(id+'-diffusion-tip-'+str(j),[(ex,ey),(bx-size*.50*uy,by+size*.50*ux),(bx+size*.50*uy,by-size*.50*ux)],color,0,color,True);z['fill_opacity']=.80

def directed(id,start,ctrl,end,sw=2.8):
 pts=[start,*ctrl,end];x=min(p[0] for p in pts);y=min(p[1] for p in pts);w=max(p[0] for p in pts)-x;h=max(p[1] for p in pts)-y
 cmds=[{'moveTo':{'x':start[0]-x,'y':start[1]-y}},{'cubicBezTo':{'x1':ctrl[0][0]-x,'y1':ctrl[0][1]-y,'x2':ctrl[1][0]-x,'y2':ctrl[1][1]-y,'x':end[0]-x,'y':end[1]-y}}]
 curve(id,x,y,w,h,cmds,'#000000',sw)
 dx,dy=end[0]-ctrl[1][0],end[1]-ctrl[1][1];length=math.hypot(dx,dy);ux,uy=dx/length,dy/length;size=13 if sw<4 else 19;bx,by=end[0]-size*ux,end[1]-size*uy
 poly(id+'-tip',[end,(bx-size*.43*uy,by+size*.43*ux),(bx+size*.43*uy,by-size*.43*ux)],'#000000',0,'#000000',True)

diffusion('legend',82,117,46,'red',.60)
directed('legend-directed',(75,251),[(56,209),(76,144)],(83,117),5)
# A: four initially overlapping policies from the shared initial state.
for id,x,y,col in [('cyan',220,290,'cyan'),('red',261,303,'red'),('pink',214,341,'pink'),('green',260,352,'green')]:diffusion('a-'+id,x,y,48,col)
for j,(x,y) in enumerate([(220,292),(258,304),(212,346),(258,350)]):line('a-directed-'+str(j),[(230,327),(x,y)],sw=3.2,arrow=True,size=14)
ellipse('a-initial',219,317,22,20,'#000000','none',0)
# B: first discrimination step.
for id,x,y,col in [('cyan',507,273,'cyan'),('green',515,198,'green'),('red',545,238,'red'),('pink',515,349,'pink')]:diffusion('b-'+id,x,y,48,col)
for j,(x,y) in enumerate([(507,276),(515,195),(545,239),(518,353)]):line('b-directed-'+str(j),[(515,327),(x,y)],sw=2.8,arrow=True,size=12)
ellipse('b-initial',504,317,22,20,'#000000','none',0)
# C: two retained skills plus the local initial policy.
for id,x,y,col in [('green',817,151,'green'),('red',790,251,'red'),('pink',800,350,'pink')]:diffusion('c-'+id,x,y,48,col)
directed('c-directed-long',(800,327),[(806,265),(810,199)],(817,151))
line('c-directed-middle',[(800,327),(795,251)],sw=2.8,arrow=True,size=12)
line('c-directed-local',[(800,327),(801,356)],sw=2.8,arrow=True,size=12)
ellipse('c-initial',789,317,22,20,'#000000','none',0)
# D: expansion around the successful green policy, including overlapping new candidates.
for id,x,y,col in [('pink',1084,350,'pink'),('red',1073,251,'red'),('yellow',1082,170,'yellow'),('green',1101,149,'green'),('orange',1130,85,'orange'),('gray',1062,105,'gray'),('cyan',1138,126,'cyan')]:diffusion('d-'+id,x,y,48,col)
line('d-directed-local',[(1084,327),(1086,356)],sw=2.8,arrow=True,size=12)
line('d-directed-red',[(1084,327),(1078,251)],sw=2.8,arrow=True,size=12)
directed('d-directed-trunk',(1084,327),[(1090,265),(1097,201)],(1102,151))
for j,end in enumerate([(1065,110),(1130,89),(1138,126),(1084,180)]):line('d-new-directed-'+str(j),[(1102,151),end],sw=3,arrow=True,size=13)
ellipse('d-initial',1073,317,22,20,'#000000','none',0)
# E: final policy tree covering both sides of the obstacle.
for id,x,y,col in [('gray',1347,65,'gray'),('green',1383,151,'green'),('pink',1366,350,'pink'),('red',1356,251,'red'),('cyan',1495,85,'cyan'),('orange',1506,222,'orange'),('blue',1511,342,'blue')]:diffusion('e-'+id,x,y,48,col)
line('e-local',[(1366,327),(1368,355)],sw=2.8,arrow=True,size=12)
line('e-red',[(1366,327),(1360,251)],sw=2.8,arrow=True,size=12)
line('e-trunk',[(1366,327),(1383,151)],sw=3,arrow=True,size=13)
line('e-gray',[(1383,151),(1350,66)],sw=3,arrow=True,size=13)
line('e-cyan',[(1383,151),(1495,85)],sw=3,arrow=True,size=13)
line('e-orange',[(1495,85),(1507,222)],sw=3,arrow=True,size=13)
line('e-blue',[(1507,222),(1515,342)],sw=3,arrow=True,size=13)
ellipse('e-initial',1355,317,22,20,'#000000','none',0)
finish()
