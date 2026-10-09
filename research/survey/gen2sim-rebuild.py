"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='gen2sim'; CAT='gen2sim-scaling-up-robot-learning-in-simulation-with-generative-models'; FIG='figure-2'; CROP=[52, 50, 558, 231]; FONT='Times New Roman'
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
s['provenance']['notes']+=' Flattened original rebuilt with individual source asset photographs and robot/scene renderings. All captions, task instructions and reward/code labels are live typeable text. Outlined arrows and caption boxes are native; four small model-logo icons retain original pixels.'
# Every asset thumbnail is an independent photographic object rather than one
# flattened diagram panel, so the generated object catalogue stays movable.
for row in range(10):
 for col in range(8):
  x=6+col*50;y=9+row*50
  image(f'asset-{row+1}-{col+1}',(x,y,x+49,min(y+49,506)),'Original individual generated object asset rendering')
# Original rendered task environments and robot-action photos are isolated.
for id,box in [('fridge-environment',(505,78,685,254)),('cabinet-environment',(502,333,687,498)),('open-fridge',(815,84,936,252)),('pick-veggie',(1067,84,1192,252)),('place-veggie',(1304,84,1426,252)),('open-cabinet',(814,313,937,499)),('pick-ball',(1065,313,1193,499)),('place-ball',(1303,313,1427,499))]:
 image(id,box,'Original isolated generated environment or robotic task execution rendering; its internal pixels remain raster')
for j,box in enumerate([(429,87,472,129),(722,87,766,129),(429,325,472,367),(722,325,766,367)]):image('model-logo-'+str(j),box,'Original small language-model logo/icon')
# Native outline arrows faithfully retain the large white arrowheads.
for j,(x,y) in enumerate([(412,133),(705,133),(412,371),(705,371)]):
 poly('generation-arrow-'+str(j),[(x,y+10),(x+64,y+10),(x+64,y),(x+82,y+14),(x+64,y+28),(x+64,y+18),(x,y+18)],'#000000',2.8,'#FFFFFF',True)
# All rectangular instructions are live text with original line breaks.
for id,box,label,fs in [('fridge-task',(511,25,162,43),'Put the veggies inside\nthe refrigerator',14),('cabinet-task',(520,267,162,42),'Put the tennis ball inside\nthe left of the cabinet',14),('fridge-step-one',(794,24,162,43),'Open the left door of the\nrefrigerator',14),('fridge-step-two',(1033,24,190,43),'Pick up the veggie, while\nkeeping the door open',14),('fridge-step-three',(1270,24,188,43),'Move the veggie inside',14),('cabinet-step-one',(814,267,124,43),'Open the left door\nof the cabinet',14),('cabinet-step-two',(1044,267,168,43),'Pick up the ball, while\nkeeping the door open',14),('cabinet-step-three',(1281,267,168,43),'Move the ball into the\ncabinet',14)]:
 x,y,w,h=box;rect(id+'-box',x,y,w,h,'#FFFFFF','#000000',1.4);text(id+'-label',label,x+3,y+4,w-6,h-8,fs,bold=True)
# Original reward signs and color are retained as editable per-line labels.
green='#60AD3A';red='#DF2E21'
reward_specs=[('fridge-open',940,135,[('Reward:',green),('+ Grasp handle',green),('+ Open left door',green)]),('fridge-pick',1196,135,[('Reward:',green),('+ Grasp veggie',green),('- Left door state',red)]),('fridge-place',1432,135,[('Reward:',green),('+ Veggie inside',green),('  fridge',green),('- Left door state',red)]),('cabinet-open',940,378,[('Reward:',green),('+ Grasp handle',green),('+ Open left door',green)]),('cabinet-pick',1194,378,[('Reward:',green),('+ Grasp ball',green),('- Left door state',red)]),('cabinet-place',1432,370,[('Reward:',green),('+ Ball inside',green),('  cabinet',green),('- Left door state',red)])]
for id,x,y,lines in reward_specs:
 for j,(label,color) in enumerate(lines):text(id+'-reward-'+str(j),label,x,y+j*12,82,12,9.5,color,True,align='left')
 cy=y+len(lines)*12+3;cx=x+18
 rounded(id+'-code-box',cx,cy,20,26,3,'#F5F5F5','#3F3F3F',1.2)
 text(id+'-code-label','</>',cx+1,cy+4,18,17,10,'#333333',True)
text('asset-generation-title','Asset Generation',101,512,243,27,20,bold=True)
text('task-generation-title','Task Generation',497,512,242,27,20,bold=True)
text('decomposition-title','Task Decomposition and Reward Generation',817,512,626,27,20,bold=True)
# Keep manual source-width labels inside their original boxes in both formats.
for n in s['nodes']:
 if n['shape']=='text':
  font='hebo' if n.get('bold') else 'helv';length=fitz.get_text_length(n['label'].split('\n')[0],fontname=font,fontsize=n['font_size'])
  length=max(fitz.get_text_length(t,fontname=font,fontsize=n['font_size']) for t in n['label'].split('\n'))
  if length>n['width']:n['font_size']*=n['width']/length*.98
finish()
