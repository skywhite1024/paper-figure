"""Manually reconstructed after inspecting original PDF raster, not automatic vectorization."""
from pathlib import Path
from PIL import Image
import json
import argparse,io,hashlib
parser=argparse.ArgumentParser(description="Rebuild RoboReact Figure 2 from its original source image or PDF")
g=parser.add_mutually_exclusive_group(required=True)
g.add_argument("--image",type=Path,help="Original 2256x1000 figure image")
g.add_argument("--pdf",type=Path,help="arXiv2608.03387v2 PDF; extracts page3 figure image")
args=parser.parse_args()
if args.pdf:
 import fitz
 doc=fitz.open(args.pdf)
 candidates=[im for im in doc[2].get_images(full=True) if im[2:4]==(2256,1000)]
 if len(candidates)!=1:raise SystemExit("Expected exactly one2256x1000 source figure on page3")
 source_bytes=doc.extract_image(candidates[0][0])["image"]
else:source_bytes=args.image.read_bytes()
source_hash=hashlib.sha256(source_bytes).hexdigest()
R=Path(__file__).resolve().parents[1]; D=R/'data/diagrams';A=D/'assets/roboreact';A.mkdir(parents=True,exist_ok=True)
source=Image.open(io.BytesIO(source_bytes))
if source.size!=(2256,1000):raise SystemExit('Source must be the original2256x1000 figure image')
s=dict(schema_version=1,id='roboreact-figure-2',title='RoboReact: Figure 2 — source-layout editable reconstruction',canvas=dict(width=2256,height=1040),provenance=dict(paper_title='RoboReact: Agentic Skill Distillation from Generated Egocentric Videos for Generalizable Whole-Body Manipulation',paper_url='https://arxiv.org/abs/2608.03387v2',pdf_url='https://arxiv.org/pdf/2608.03387v2',figure='Figure 2',page=3,license='arXiv non-exclusive distribution license; no open reuse license verified. Private user-requested adaptation, not permission for public redistribution. https://arxiv.org/licenses/nonexclusive-distrib/1.0/',status='figure_recreation',notes='Reconstructed from actual original figure pixels. Original panel arrangement, labels, colors, graph topology and photo panels retained closely. Panels, ordinary labels, graph nodes and connections are native editable objects; photos, decorative icons, compact formula strips and diagnostic overlays remain raster crops. Font and curve geometry approximated. Original figure is a single 2256×1000 raster in the PDF, not extractable vector artwork.',caption='Overview of RoboReact.',source_bbox_pdf_points=[54,54.003,557.9904,277.403],visual_inspection='Source PDF page 3 and extracted original 2256×1000 figure inspected 2026-10-09',omitted_details=['No omitted method stages or photographs','Some tiny diagnostic overlay text remains embedded in raster panels','Curve curvature, exact fonts and individual dash lengths approximated']),nodes=[],edges=[])
s['provenance']['source_image_sha256']=source_hash
# Coordinates authored on half-size source display; converted to original 2256px coordinates.
def n(id,label,x,y,w,h,fill='#FFFFFF',stroke='#FFFFFF',shape='rect',fs=12,**kw):
 s['nodes'].append(dict(id=id,label=label,x=x*2,y=y*2,width=w*2,height=h*2,fill=fill,stroke=stroke,shape=shape,font_size=fs*2,**kw));return id
def t(id,label,x,y,w,h,fs=12,color='#101010',bold=False,italic=False):return n(id,label,x,y,w,h,shape='text',fs=fs,text_color=color,bold=bold,italic=italic,font_family='Arial',align='center')
def e(id,a,b,color='#216E89',sp='right',tp='left',arrow=True,waypoints=None,**kw):s['edges'].append(dict(id=id,source=a,target=b,source_port=sp,target_port=tp,arrow=arrow,stroke=color,stroke_width=1.1,waypoints=[dict(x=x*2,y=y*2) for x,y in (waypoints or [])],**kw))
def img(id,box,alt=None):
 x,y,x1,y1=box;source.crop(tuple(round(v*2) for v in box)).save(A/(id+'.png'));return n(id,'',x,y,x1-x,y1-y,shape='image',asset='assets/roboreact/'+id+'.png',alt=alt or ('Original raster detail: '+id),editable=False)
def anchor(id,x,y):return n(id,'',x,y,.1,.1,fill_opacity=0)
def line(id,points,color='#216E89',arrow=False,dash=False):
 a=anchor(id+'-a',*points[0]);b=anchor(id+'-b',*points[-1]);e(id,a,b,color,arrow=arrow,waypoints=points[1:-1],dash=dash)
def circle(id,x,y,r=6,fill='#8FD26B',stroke='#337897'):return n(id,'',x-r,y-r,r*2,r*2,fill,stroke,'ellipse',stroke_width=.8)
# Main and nested panels are placed before labels and data.
for id,x,y,w,h,f,c in [('inputs',6,6,267,145,'#E9E9E9','#DCDCDC'),('gen',6,153,267,232,'#FBF6FF','#E1DDE5'),('recover',296,6,263,379,'#F5FBF6','#EBF1EC'),('solver',843,5,280,376,'#E0ECF8','#D6E0EB'),('execution',6,390,1117,104,'#FFFAF1','#EAE5DC')]:n(id,'',x,y,w,h,f,c,'rounded_rect')
for id,x,y,w,h in [('input-rgb',10,40,133,98),('input-lang',146,40,123,98)]:n(id,'',x,y,w,h,'#F6FAFF','#F6FAFF','rounded_rect')
for id,x,y,w,h in [('recover-images',303,61,249,133),('keypoint-panel',303,221,249,59),('object-panel',303,304,249,75)]:n(id,'',x,y,w,h,'#F7FCF8','#ECF3ED','rounded_rect')
for i in range(4):n('policy-bg'+str(i),'',579,43+i*64,216,62,'#F4F9FF','#F4F9FF','rounded_rect')
n('policy-bg4','',579,315,216,62,'#FFFAF1','#E8E2D8','rounded_rect')
n('rollout-bg','',851,77,126,92,'#F8FCFF','#F8FCFF','rounded_rect');n('editor-bg','',851,190,266,80,'#F8FCFF','#F8FCFF','rounded_rect');n('diag-bg','',856,210,117,54,'#FFFFFF','#FFFFFF','rounded_rect');n('edit-bg','',982,210,130,54,'#FFFFFF','#FFFFFF','rounded_rect');n('valid-bg','',851,313,266,61,'#F8FCFF','#F8FCFF','rounded_rect')
# All actual source photographic panels retained as cropped images.
for id,box in [('input-rgb-photo',(13,76,72,127)),('input-depth-photo',(76,76,139,127)),('depth',(322,76,408,127)),('wrist',(440,76,532,128)),('hand',(323,142,364,188)),('skeleton',(367,143,409,188)),('object-poses',(440,142,532,189)),('selected-1',(35,318,88,381)),('selected-2',(93,318,147,381)),('selected-3',(151,318,205,381)),('selected-4',(209,318,263,381)),('alignment-photo',(337,336,371,367)),('execution-poses',(204,417,328,488)),('execution-align-human',(424,417,499,488)),('execution-align-robot',(550,417,631,488)),('execution-controller',(732,417,827,488)),('execution-complete',(959,417,1046,488))]:img(id,box)
# Small icons are separate movable raster assets; their internal artwork is not editable.
for id,box in [('vlm-icon',(17,270,58,317)),('candidate-camera1',(82,237,122,267)),('candidate-camera2',(145,237,185,267)),('candidate-camera3',(213,237,253,267)),('selection-cross1',(116,267,131,282)),('selection-check',(175,266,193,282)),('selection-cross3',(244,266,259,282)),('rollout-rgb-icon',(866,86,902,113)),('rollout-hand-icon',(927,83,952,114)),('rollout-ee-icon',(867,134,906,155)),('rollout-object-icon',(931,131,954,155)),('completion-check',(1046,439,1094,485))]:img(id,box)
# Editable headings, input labels and original example instruction.
t('inputs-title','Inputs',10,13,258,20,16,bold=True)
t('rgb-title','RGB-D Observation',12,48,128,20,12)
t('lang-title','Language Instruction',145,48,125,20,12)
t('instruction','Open the drawer,\nplace the blue\ncylinder inside,\nthen close it.',151,71,111,59,12,italic=True)
for id,k,x,y,c in [('stage1','1',19,165,'#793AC1'),('stage2','2',309,19,'#00852A'),('stage3','3',865,23,'#17617F'),('stage4','4',24,438,'#B87315')]:circle(id,x,y,10,c,c);t(id+'label',k,x-8,y-8,16,16,14,'#FFFFFF',True)
t('gen-heading','Generate &\nSelect Ego-centric Video',45,156,215,38,16,'#793AC1',True)
t('candidates-title','Ego-centric Video Candidates',53,202,210,18,12,italic=True)
t('vlm-label','VLM Scorer\n(frozen)',8,240,72,30,12,bold=True)
for i,x in enumerate([82,145,211]):circle('candidate-index'+str(i),x,230,8,'#793AC1','#793AC1');t('candidate-index-label'+str(i),str(i+1),x-6,223,12,14,12,'#FFFFFF',True)
t('selected-label','Selected video',96,299,127,18,12,italic=True)
line('select-arrow',[(159,278),(159,296)],'#793AC1',True)
t('recover-heading','Recover & Build\nObject-Centric Keyframe Policy',321,6,230,38,16,'#00852A',True)
t('recover-subheading','Recover from Selected Video',319,46,219,17,12,'#00852A',True)
for id,label,x,y,w in [('depth-label','Metric Depth',322,62,85),('wrist-label','Wrist Motion',440,62,91),('hand-label','Hand Motion',322,128,87),('object-label','Object Poses',440,128,92)]:t(id,label,x,y,w,15,12,italic=True)
t('keypoint-title','Keypoint Selection and Encoding',312,198,221,17,12,'#00852A',True)
t('object-title','Object-Centric Representation',321,285,212,17,12,'#00852A',True)
line('recover-down',[(520,194),(520,211)],'#8AD36C',True);line('keypoint-down',[(520,280),(520,299)],'#8AD36C',True)
# Keypoint encoding retains exact visible source count and gap placements.
for i,x in enumerate([318,339,360,380,402,423,506,527]):circle('kp'+str(i),x,245,6,'#F7FCF8' if i in [2,7] else '#97D879')
for i in range(5):e('kp-edge'+str(i),'kp'+str(i),'kp'+str(i+1),arrow=False)
e('kp-complete','kp6','kp7',arrow=False)
t('kp-ellipsis1','…',389,217,28,16,15);t('kp-ellipsis2','……',444,236,42,17,14)
t('approach-label','Approach',326,214,64,15,11,italic=True);t('contact-label','Contact',339,260,50,15,11,italic=True);t('complete-label','Completion',447,260,65,15,11,italic=True)
line('approach-pointer',[(319,217),(319,237)],arrow=True);line('approach-pointer2',[(380,216),(380,237)],arrow=True);line('contact-pointer',[(339,265),(339,252)],arrow=True);line('completion-pointer',[(506,266),(506,252)],arrow=True)
# Object-centered example graph native objects; small alignment image retained.
obj=[(319,330),(356,314),(385,330),(408,359),(440,319),(485,351),(527,337)]
for i,(x,y) in enumerate(obj):circle('obj'+str(i),x,y,7)
for i,j in [(0,1),(1,2),(2,3),(3,4),(4,5)]:e('obj-edge'+str(i),'obj'+str(i),'obj'+str(j),arrow=True,dash=i<2)
t('object-ellipsis','…',494,334,24,16,14);t('object-align-label','Object-based alignment',307,368,155,14,10,italic=True)
line('alignment-pointer',[(354,320),(349,335)],arrow=True)
# Interstage source routing.
line('selected-to-recover',[(267,356),(291,356),(291,119),(315,119)],arrow=True)
line('recover-to-policy',[(556,344),(564,344),(564,71),(579,71)],arrow=True)
# Legend and exact five policy-state layouts. Graph circles/lines are individually editable.
circle('success-key',586,27,7,'#66AD83');t('success-label','Success',595,19,56,18,11)
circle('fail-key',684,27,7,'#FF8B84');t('fail-label','Fail',694,19,35,18,11)
policy_points=[[(588,67),(609,52),(616,69),(610,96),(644,59),(674,83),(710,60),(736,90),(780,81)],[(588,131),(609,116),(616,133),(610,160),(644,124),(674,147),(710,125),(736,153),(780,145)],[(588,195),(609,180),(616,197),(610,224),(644,188),(679,181),(709,190),(736,218),(780,208)],[(588,259),(609,244),(616,261),(610,288),(644,252),(679,246),(709,254),(744,259),(736,283),(780,273)],[(588,339),(609,324),(616,341),(610,366),(644,332),(676,336),(709,344),(744,345),(780,345)]]
greens=[set(),{0,1,4},{0,1,3,4,5,6},{0,1,2,3,4,5,6,7,8},set(range(9))]
for row,pts in enumerate(policy_points):
 for k,(x,y) in enumerate(pts):circle(f'p{row}-{k}',x,y,7,'#68AD85' if k in greens[row] else '#FF8A85')
 # Repeated dotted initial keyframe neighborhood retained.
 for z,(a,b) in enumerate([(0,1),(0,2),(0,3),(1,4),(2,4),(3,4)]):e(f'p{row}-cluster{z}',f'p{row}-{a}',f'p{row}-{b}',arrow=False,dash=True)
 chain=list(range(4,len(pts)-1))
 for k in chain:e(f'p{row}-seq{k}',f'p{row}-{k}',f'p{row}-{k+1}',arrow=True,dash=(row==3 and k==5))
 t('p-label'+str(row),['Π⁰','Π¹','Π²','Π³','Π*'][row],766,[44,108,172,236,316][row],30,20,16,'#FF0000' if row==4 else '#000000',True)
 t('cluster-ellipsis'+str(row),'…',614,[78,142,206,270,349][row],18,15,12,'#62A436' if row==4 else '#FF0000',True)
 t('policy-end-ellipsis'+str(row),'…',751,[79,143,207,271,337][row],23,18,16)
# Tiny faded old targets and modified-label annotations.
circle('offset-old',674,212,7,'#F6DFE3','#F6DFE3');line('offset-ghost',[(679,189),(674,212)],'#BBD9EA',dash=True);t('offset-label','Offset',674,191,45,16,11,italic=True);t('insert-label','Insert',720,237,41,16,11,italic=True)
t('policy-more','⋮',680,291,16,25,19)
# Curved solver iteration arrows retained as separate raster icons (no labels baked in).
for id,box in [('offset-curve',(800,89,839,127)),('insert-curve',(800,153,839,191)),('delete-curve',(800,216,839,255)),('more-curve',(800,271,839,307))]:img(id,box)
for id,label,y in [('offset','Offset',138),('insert','Insert',194),('delete','Delete',257)]:t(id+'-action',label,799,y,42,16,11)
t('solver-more','⋮',813,307,16,29,20)
# Solver exact native labels and cropped mathematical formula details.
t('solver-heading','In-Context Optimization Solver\n(Sequential Refinement)',878,6,237,40,16,'#17617F',True)
t('rollout-heading','Rollout Rⁿ from Πₙ',855,57,127,17,12,'#17617F',True)
t('memory-heading','Rollout Memory Mⁿ⁺¹',983,57,133,17,12,'#17617F',True)
for id,label,x,y,w in [('rgb-icon-label','RGB',869,116,37),('hand-icon-label','Hand Action',913,116,59),('ee-icon-label','EE Pose',868,155,42),('object-icon-label','Object Pose',914,155,63)]:t(id,label,x,y,w,13,9,bold=True)
for id,label,y in [('memory-rgb','RGB (ego / third-person)',78),('memory-pose','Object + EE pose',99),('memory-gripper','Gripper + proprioception',127),('memory-update','Mⁿ⁺¹ = Mⁿ ∪ {Rⁿ}',148)]:n(id,label,993,y,110,18,'#70AFC5','#3D798D','rounded_rect',8,text_color='#FFFFFF',bold=True)
t('memory-ellipsis','…',1041,116,16,11,11,bold=True)
line('memory-flow',[(976,123),(992,123)],'#A6CCE9',True);line('memory-editor',[(1069,170),(1069,188)],'#A6CCE9',True)
t('editor-heading','Frozen VLM Editor ΔΠⁿ',882,174,216,18,13,'#17617F',True)
t('diagnose-heading','Diagnose',875,193,87,17,11,'#17617F',True);t('edit-heading','Edit',1006,193,69,17,11,'#17617F',True)
t('diagnose-list','•  Success\n    …\n•  Alignment\n•  Infeasible',862,212,99,49,9)
t('edit-list','•  Keep\n•  Align\n•  Offset\n•  Insert\n•  Delete',989,212,114,49,8)
img('editor-equation',(894,275,1044,292),'Original raster equation; mathematical notation remains raster')
t('validator-heading','Validator + Projection ProjF',880,296,226,16,13,'#17617F',True)
line('editor-validator',[(1069,273),(1069,311)],'#A6CCE9',True)
for id,label,x,y,w in [('valid-reground','Object-Centric Re-ground',866,319,118),('valid-bound','Bound / IK',995,319,105),('valid-clearance','Approach Clearance',866,347,118),('valid-more','…',995,347,105)]:n(id,label,x,y,w,19,'#70AFC5','#70AFC5','rounded_rect',9,text_color='#FFFFFF',bold=True)
# Execution phase layout and original images; arrows are editable.
t('execution-heading','Execution\n(Frozen Policy)',39,423,123,41,16,'#B87315',True)
for id,label,x,w in [('estimate-heading','Estimate Object Poses in New Scene',160,233),('reground-heading','Re-ground Aligned Keyframes',411,238),('controller-heading','Whole-Body Controller Tracking',695,218),('completion-heading','Task Completion',941,128)]:t(id,label,x,396,w,18,12,'#B87315',True)
for id,pts in [('exec-arrow1',[(339,452),(419,452)]),('exec-arrow2',[(504,452),(541,452)]),('exec-arrow3',[(638,451),(719,451)]),('exec-arrow4',[(837,449),(956,449)])]:line(id,pts,'#B87315',True)
line('policy-execution',[(689,369),(689,401)],'#B87315',True)
t('credit','Source-layout reconstruction of He et al., RoboReact (2026), Figure 2, p. 3 · Native labels, panels and graph elements; photos, icons and equation strip remain raster · Private user-requested adaptation',6,502,1117,15,8,'#444444')
(D/'roboreact-figure-2.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
print(len(s['nodes']),'nodes',len(s['edges']),'edges',sum(n['shape']=='image' for n in s['nodes']),'raster assets')
# Post-preview fidelity corrections: text fitting and native broad arrows.
s['nodes']=[z for z in s['nodes'] if z['id'] not in {'offset-curve','insert-curve','delete-curve','more-curve'}]
for z in s['nodes']:
 if z['id']=='recover-heading':z.update(x=318*2,y=5*2,width=237*2,height=38*2,font_size=14*2,no_wrap=True)
 if z['id']=='recover-subheading':z['y']=47*2
for z in s['edges']:
 if z['id'].startswith('exec-arrow'):z['stroke_width']=7
 elif z['id'] in ['selected-to-recover','recover-to-policy']:z['stroke_width']=4
 elif z['id'] in ['recover-down','keypoint-down','select-arrow','memory-flow','memory-editor','editor-validator']:z['stroke_width']=6
s['edges']=[z for z in s['edges'] if z['id']!='policy-execution']
def path(id,x,y,w,h,commands,fill,stroke=None):
 scaled=[]
 for cmd in commands:
  op,points=next(iter(cmd.items()));scaled.append({op:{k:v*2 for k,v in points.items()}})
 n(id,'',x,y,w,h,fill,stroke or fill,'path',commands=scaled,stroke_width=1)
for id,y in [('offset-curve',92),('insert-curve',156),('delete-curve',220),('more-curve',274)]:
 path(id,803,y,36,36,[{'moveTo':{'x':0,'y':0}},{'cubicBezTo':{'x1':29,'y1':0,'x2':39,'y2':9,'x':35,'y':17}},{'cubicBezTo':{'x1':30,'y1':24,'x2':18,'y2':27,'x':9,'y':28}},{'lineTo':{'x':10,'y':35}},{'lineTo':{'x':0,'y':26}},{'lineTo':{'x':10,'y':18}},{'lineTo':{'x':9,'y':23}},{'cubicBezTo':{'x1':25,'y1':21,'x2':33,'y2':17,'x':33,'y':14}},{'cubicBezTo':{'x1':29,'y1':9,'x2':15,'y2':7,'x':0,'y':7}},{'close':{}}],'#5999AF')
path('policy-execution-arrow',675,369,28,37,[{'moveTo':{'x':7,'y':0}},{'lineTo':{'x':21,'y':0}},{'lineTo':{'x':21,'y':23}},{'lineTo':{'x':28,'y':23}},{'lineTo':{'x':14,'y':37}},{'lineTo':{'x':0,'y':23}},{'lineTo':{'x':7,'y':23}},{'close':{}}],'#B87315','#645340')
s['provenance']['notes']=s['provenance']['notes'].replace('decorative icons, compact formula strips','decorative icons, compact formula strips')
(D/'roboreact-figure-2.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
print('After visual QA:',len(s['nodes']),'nodes',len(s['edges']),'edges',sum(n['shape']=='image' for n in s['nodes']),'raster assets')
# Keep the validator arrow clear of the native heading; retain explicit raster annotation caveats.
for z in s['nodes']:
 if z['id']=='validator-heading':z.update(x=880*2,width=184*2,font_size=12*2,no_wrap=True)
 if z['id'] in ['diagnose-list','edit-list']:z['align']='left';z['x']+=16;z['width']-=16
s['provenance']['raster_details']=['17 photographic/depth/pose source panels retained as individual crops; their pixel contents and diagnostic overlays are not editable','12 decorative source icon/mark crops remain raster','1 mathematical editor-update equation strip remains raster; its symbols are not editable','All four blue iteration arrows and the large orange execution arrow are native freeform paths','Policy graph nodes/edges use native shapes/connectors; small curves and dash spacing approximate the source']
(D/'roboreact-figure-2.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
used={Path(z['asset']).name for z in s['nodes'] if z['shape']=='image'}
for f in A.glob('*.png'):
 if f.name not in used:f.unlink()
# Match terminal ellipsis continuation instead of inventing a solid final arrow.
for row,pts in enumerate(policy_points):
 s['edges']=[z for z in s['edges'] if z['id']!=f'p{row}-seq{len(pts)-2}']
s['provenance']['notes']=s['provenance']['notes'].replace('graph topology','graph progression')
(D/'roboreact-figure-2.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
