"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='robogen'; CAT='robogen-towards-unleashing-infinite-data-for-automated-robot-learning-via-generative-simulation'; FIG='figure-2'; CROP=[79, 66, 519, 257]; FONT='Times New Roman'
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
FONT='Courier New'
s['provenance']['notes']+=' Initialization asset icons, scene photographs and each skill thumbnail are separate original raster crops. All stage headings, task-example cards, models, configuration blocks, dataset labels, reward labels and main routing paths are native typeable/editable objects.'
yellow='#FFFAE7';mint='#EBFFEE';sky='#E5F5FD';pink='#FDE6DF';blue='#356B96';black='#161616'
for id,x,y,w,h,c in [('initialization',21,50,297,321,yellow),('proposals',21,384,297,178,yellow),('generation',348,49,461,321,mint),('population',348,401,461,163,mint),('supervision',842,49,465,309,sky),('learning',844,403,466,162,pink)]:rounded(id,x,y,w,h,9,c,black,2)
for id,x,y,w,label in [('stage-a',58,8,210,'A) Task Proposal'),('stage-b',465,9,231,'B) Scene Generation'),('stage-c',902,9,345,'C) Training Supervision Generation'),('stage-d',980,364,176,'D) Skill Learning')]:
 rect(id,x,y,w,32,'#FFFFFF',black,2);text(id+'-label',label,x+2,y+1,w-4,30,22,italic=True,font='Arial')
for id,label,x,y,w in [('initial-heading','Initialization',63,55,215),('proposal-heading','Task Proposals',65,389,211),('configuration-heading','Scene Components & Configuration',393,54,386),('population-heading','Scene Population',454,409,250),('decomposition-heading','Task Decomposition',979,61,251),('reward-heading','Reward Generation',920,310,244)]:text(id,label,x,y,w,28,20,bold=True)
text('robot-label','a) Robot',41,86,124,25,18,align='left');text('object-label','b) Object',42,193,132,25,18,align='left')
for id,box in [('robot-arm',(62,119,120,177)),('robot-small',(144,122,198,177)),('quadruped',(217,121,280,178)),('microwave',(40,229,98,282)),('arm-object',(112,221,164,283)),('sanitizer',(182,221,229,281)),('suitcase',(247,220,306,282)),('dishwasher',(40,292,98,350)),('safe',(111,294,167,350)),('laptop',(179,293,234,351)),('cabinet',(245,291,309,351))]:image(id,box,'Original robot/object asset icon; internal pixels remain raster')
def model(id,x,y,w=44,h=35,label='LLM',c='#AEDAFB'):
 rect(id,x,y,w,h,c,'#4C88AC',1.8);text(id+'-label',label,x,y+3,w,h-6,18,'#356B96',font='Arial')
model('task-llm',34,465,43,33);model('scene-llm',580,81,42,33);model('supervision-llm',858,83,42,33);model('reward-llm',991,259,42,34)
for id,x,y,w,lab in [('proposal1',176,415,124,'“Retrive one gold bar\nand lock the safe”'),('proposal2',166,457,140,'“Heat up a bowl of soup\nusing the microwave”'),('proposal3',175,499,123,'“Close the laptop lid”'),('proposal4',176,527,121,'“Climb up the stairs”')]:
 rect(id,x,y,w,34 if id in ['proposal1','proposal2'] else 21,'#EFFFFF',black,1.5);text(id+'-label',lab,x+2,y+1,w-4,32 if id in ['proposal1','proposal2'] else 19,13,italic=True,font='Arial')
text('proposal-ellipsis','......',216,548,33,14,11)
for k,y in enumerate([429,470,509,537]):
 curve('proposal-flow-'+str(k),77,min(483,y),98,abs(483-y)+.1,[{'moveTo':{'x':0,'y':483-min(483,y)}},{'cubicBezTo':{'x1':38,'y1':483-min(483,y),'x2':46,'y2':y-min(483,y),'x':98,'y':y-min(483,y)}}],blue,1.8)
 line('proposal-tip-'+str(k),[(164,y),(175,y)],blue,1.8,True,size=7)
line('proposal-init-robot',[(40,99),(9,99),(9,484),(34,484)],black,1.8,False,size=7)
line('proposal-init-robot-arrow',[(40,99),(9,99)],black,1.8,True,size=7)
line('proposal-init-llm-arrow',[(24,484),(34,484)],black,1.8,True,size=7)
line('proposal-init-object',[(40,204),(9,204)],black,1.8,True,size=7)
line('proposal-to-scenes',[(318,484),(335,484),(335,98),(578,98)],black,1.8,True,size=7)
for id,x,w,label in [('relevant-assets',357,87,'Relevant\nAssets'),('asset-sizes',461,62,'Asset\nSizes'),('asset-configuration',539,120,'Asset\nConfiguration'),('scene-configuration',675,128,'Scene\nConfiguration')]:
 rounded(id,x,153,w,40,6,'#F5E5F7',black,2);text(id+'-label',label,x+2,156,w-4,33,17)
 cx=x+w/2
 curve(id+'-input',min(cx,601),113,abs(cx-601)+1,40,[{'moveTo':{'x':601-min(cx,601),'y':0}},{'cubicBezTo':{'x1':601-min(cx,601),'y1':22,'x2':cx-min(cx,601),'y2':11,'x':cx-min(cx,601),'y':37}}],blue,1.7)
 line(id+'-input-tip',[(cx,145),(cx,151)],blue,1.7,True,size=6)
 curve(id+'-output',min(cx,617),194,abs(cx-617)+1,39,[{'moveTo':{'x':cx-min(cx,617),'y':0}},{'cubicBezTo':{'x1':cx-min(cx,617),'y1':32,'x2':617-min(cx,617),'y2':4,'x':617-min(cx,617),'y':37}}],blue,1.6)
rounded('retrieval-box',495,234,304,123,14,'#FFFFFF','#222222',1.4,dash=True)
text('retrieval-title','Dataset Retrieval',540,238,215,24,17)
text('objaverse','Objaverse',582,262,140,32,27,'#B75C9D',True,font='Arial')
text('generation-method','text-to-image-to-3D generation',516,300,273,26,16)
image('midjourney-logo',(512,329,531,350),'Original tiny Midjourney sail mark')
text('midjourney','Midjourney',533,328,100,26,19,bold=True,font='Arial')
text('zero-one-three','Zero-1-to-3',690,329,101,24,16,bold=True)
line('method-flow',[(648,341),(673,341)],black,1.5,True,size=7)
rect('verify-model',408,268,43,35,'#FFECB5','#E8A13E',1.5);text('verify-model-label','VLM',408,270,43,31,19,'#DE8C27',font='Arial')
curve('verify-loop',389,243,74,84,[{'moveTo':{'x':73,'y':16}},{'cubicBezTo':{'x1':21,'y1':-31,'x2':-31,'y2':41,'x':17,'y':78}},{'cubicBezTo':{'x1':42,'y1':95,'x2':57,'y2':73,'x':72,'y':68}}],'#DE9B3F',2)
line('verify-tip',[(454,319),(462,311)],'#DE9B3F',1.7,True,size=7)
text('verification-label','Verification',359,328,135,29,19,bold=True)
line('generation-to-population',[(580,371),(580,399)],black,1.7,True,size=8)
for id,box in [('scene1',(363,446,464,547)),('scene2',(478,446,579,547)),('scene3',(591,445,692,547)),('scene4',(701,445,801,546))]:image(id,box,'Original generated scene photo; internal scene pixels remain raster')
line('scene-to-supervision',[(810,484),(826,484),(826,99),(855,99)],black,1.8,True,size=8)
line('scene-to-reward',[(826,276),(872,276)],black,1.8,True,size=8)
for id,x,y,w,h,label,c in [('grasp',915,94,62,39,'Grasp\nDoor','#F6D5D3'),('open',1000,94,62,39,'Open\nDoor','#F6D5D3'),('inside',1086,94,76,39,'Put bowl\ninside','#F6D5D3'),('timer',1184,94,61,39,'Set\nTimer','#F6D5D3'),('rl',853,176,124,39,'Reinforcement\nLearning','#FFF8C7'),('gradient',998,176,115,39,'Gradient\nOptimization','#FFF8C7'),('primitives',1134,176,159,39,'Action Primitive\n& Motion Planning','#FFF8C7'),('scene-state',874,251,65,48,'Scene\nstate','#ECFBE9'),('reward',1074,251,85,48,'','#ECFBE9')]:
 rounded(id,x,y,w,h,6,c,black,2);text(id+'-label',label,x+1,y+3,w-2,h-6,17)
text('reward-R','R',1078,261,22,27,23,italic=True,font='Times New Roman');text('reward-subscript','open_door',1092,272,64,17,15,font='Times New Roman')
text('task-chain-ellipsis','...',1270,103,26,25,18)
for k,pts in enumerate([[(900,101),(912,115)],[(978,112),(998,119)],[(1063,112),(1084,120)],[(1164,112),(1182,119)],[(1248,109),(1268,119)]]):line('task-chain-'+str(k),pts,blue,1.5,True,size=6)
rounded('select',1008,138,48,20,5,'#FFFFFF',black,1.5);text('select-label','Select',1009,138,46,20,13)
for id,pts in [('select-rl',[(1015,155),(914,173)]),('select-gradient',[(1036,158),(1048,174)]),('select-primitive',[(1055,151),(1216,173)]),('state-to-llm',[(941,276),(988,276)]),('llm-to-reward',[(1035,276),(1072,276)])]:line(id,pts,blue,1.7,True,size=7)
curve('rl-to-reward',910,216,96,41,[{'moveTo':{'x':0,'y':0}},{'cubicBezTo':{'x1':23,'y1':37,'x2':73,'y2':12,'x':96,'y':41}}],blue,1.8)
curve('gradient-to-reward',1011,218,50,38,[{'moveTo':{'x':50,'y':0}},{'cubicBezTo':{'x1':48,'y1':25,'x2':9,'y2':31,'x':0,'y':38}}],blue,1.8)
line('rl-reward-tip',[(1000,248),(1006,257)],blue,1.5,True,size=7);line('gradient-reward-tip',[(1019,249),(1011,257)],blue,1.5,True,size=7)
curve('reward-to-learning',1161,272,65,122,[{'moveTo':{'x':0,'y':0}},{'cubicBezTo':{'x1':61,'y1':14,'x2':66,'y2':72,'x':64,'y':122}}],blue,1.8)
curve('primitive-to-learning',1233,218,19,176,[{'moveTo':{'x':0,'y':0}},{'cubicBezTo':{'x1':42,'y1':53,'x2':2,'y2':86,'x':2,'y':176}}],blue,1.8)
line('reward-learning-tip',[(1225,384),(1225,398)],blue,1.6,True,size=8);line('primitive-learning-tip',[(1235,384),(1235,398)],blue,1.6,True,size=8)
for row,y,xs in [(0,431,[930,988,1046,1103,1161,1219]),(1,483,[902,960,1018,1076,1134,1193,1250]),(2,535,[933,991,1048,1106,1163,1220])]:
 for j,x in enumerate(xs):image(f'skill-{row}-{j}',(x-24,y-24,x+24,y+24),'Original isolated circular skill-execution photo; its pixels and round crop remain raster')
# Source labels remain inside their own configuration/method cards.
fit_ids={'verification-label','generation-method','rl-label','gradient-label','primitives-label','asset-configuration-label','scene-configuration-label','stage-c-label'}
font=fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf')
heading_font=fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf')
for n in s['nodes']:
 if n['id'] in fit_ids:
  label_font=heading_font if n['id']=='stage-c-label' else font
  width=max(label_font.text_length(line,fontsize=n['font_size']) for line in n['label'].split('\n'))
  n['font_size']*=min(1,(n['width']-5)/max(width,.01))
finish()
