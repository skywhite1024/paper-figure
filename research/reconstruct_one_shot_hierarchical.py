"""Manual native reconstruction of the inspected flattened Figure 2."""
import json,math,fitz
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];cid='one-shot-hierarchical-imitation-learning-of-compound-visuomotor-tasks';s=json.loads((ROOT/'research/survey'/f'{cid}.json').read_text());out=ROOT/'data/diagrams/one-shot-hierarchical';out.mkdir(parents=True,exist_ok=True)
pdf=Path(s['pdf_path']);pdf=pdf if pdf.is_absolute() else ROOT/pdf
page=fitz.open(pdf)[2];page.get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(66,48,544,224)).save(out/'one-shot-hierarchical-figure-2-original.png');im=Image.open(out/'one-shot-hierarchical-figure-2-original.png');nodes=[]
def text(id,label,x,y,w,h=28,size=22,color='#111111',bold=False,italic=False,rotation=0):
 nodes.append(dict(id=id,shape='text',label=label,x=x,y=y,width=w,height=h,font_family='Arial',font_size=size,text_color=color,align='center',bold=bold,italic=italic,no_wrap=True,text_inset=0,rotation=rotation))
def path(id,commands,color='#287BBE',width=2,fill='none',dash=False):nodes.append(dict(id=id,shape='path',x=0,y=0,width=1434,height=540,commands=commands,fill=fill,stroke=color,stroke_width=width,dash=dash))
def line(id,x1,y1,x2,y2,color='#287BBE',width=2,arrow=False,dash=False):
 path(id,[{'moveTo':dict(x=x1,y=y1)},{'lineTo':dict(x=x2,y=y2)}],color,width,dash=dash)
 if arrow:
  a=math.atan2(y2-y1,x2-x1);length=9
  path(id+'-head',[{'moveTo':dict(x=x2-length*math.cos(a-.5),y=y2-length*math.sin(a-.5))},{'lineTo':dict(x=x2,y=y2)},{'lineTo':dict(x=x2-length*math.cos(a+.5),y=y2-length*math.sin(a+.5))}],color,width)
def curve(id,x,y,c1x,c1y,c2x,c2y,ex,ey,color='#111111',width=4):
 path(id,[{'moveTo':dict(x=x,y=y)},{'cubicBezTo':dict(x1=c1x,y1=c1y,x2=c2x,y2=c2y,x=ex,y=ey)}],color,width)
 a=math.atan2(ey-c2y,ex-c2x);ln=13 if width>2 else 9
 path(id+'-head',[{'moveTo':dict(x=ex-ln*math.cos(a-.5),y=ey-ln*math.sin(a-.5))},{'lineTo':dict(x=ex,y=ey)},{'lineTo':dict(x=ex-ln*math.cos(a+.5),y=ey-ln*math.sin(a+.5))}],color,width)
rects=[(240,49,323,113),(330,49,414,113),(422,49,507,113),(536,49,622,113),(628,49,713,113),(720,49,806,113),(244,260,375,358),(375,260,508,358),(530,260,662,358),(662,260,794,358),(874,97,976,222),(985,97,1092,222),(1101,97,1202,222),(1213,97,1317,222),(1325,97,1429,222),(883,385,985,496),(993,385,1095,496),(1102,385,1205,496),(1214,385,1316,496),(1325,385,1429,496),(528,415,775,465)]
for i,(x,y,r,b) in enumerate(rects):
 name=f'frame-{i}.png';im.crop((x,y,r,b)).save(out/name);nodes.append(dict(id=f'frame-{i}',shape='image',asset=name,alt='Original mathematical objective; raster, not live equation' if i==20 else 'Original individual demonstration video frame',x=x,y=y,width=r-x,height=b-y))
line('divider-left',212,4,212,510,'#111111',2,dash=True);line('divider-right',828,4,828,510,'#111111',2,dash=True)
text('collect','Collect Demos of',5,165,200,27,23,bold=True);text('collect2','Primitive Skills',5,195,200,27,23,bold=True);text('objects','(with training objects)',4,226,204,26,20,'#666666')
curve('collect-upper',127,157,143,103,186,83,232,77);curve('collect-lower',129,264,141,306,183,326,238,321)
text('phase-title','Learning Phase Predictors',284,0,473,35,25,bold=True)
text('meta-title','Domain-Adaptive Meta-Learning',296,220,503,34,25,bold=True)
for i,(x,y,w) in enumerate([(253,121,230),(555,121,231)]):nodes.append(dict(id='phase-bg'+str(i),shape='rect',x=x,y=y,width=w,height=26,fill='#ECECEC',stroke='none'))
text('phase-human','LSTM phase predictor φₕ',253,119,230,29,20,'#CC3388',bold=True,italic=True)
text('phase-robot','LSTM phase predictor φᵣ',555,119,231,29,20,'#347C28',bold=True,italic=True)
for i,(x,t) in enumerate([(281,'0.1'),(372,'1.0'),(463,'2.0'),(575,'0.5'),(670,'3.0'),(764,'7.0')]):
 line('phase-above'+str(i),x,113,x,120);line('phase-arrow'+str(i),x,146,x,165,arrow=True);text('time'+str(i),'t='+t,x-38,169,76,28,19,bold=True)
text('human-primitives','human primitives',264,361,225,29,20,'#666666',True);text('robot-primitives','robot primitives',548,361,225,29,20,'#666666',True)
line('human-meta',428,390,522,421);line('robot-meta',617,390,522,421);line('meta-down',522,421,522,463,arrow=True)
text('learn-policy-prefix','learn how to',274,470,123,29,19,'#666666');text('learn-policy-emphasis','learn a policy',395,470,137,29,19,'#E94A2C',bold=True,italic=True);text('learn-policy-suffix','from one human primitive',532,470,258,29,19,'#666666')
text('oneshot-title','One-Shot Skill Composition',961,0,405,35,25,bold=True)
text('provide','provide video of human performing compound task',850,38,577,30,23,'#666666')
text('segment','segment video into primitives w/',903,71,305,27,20,'#666666');text('predictor-human','phase predictor φₕ',1204,71,223,27,20,'#CC3388',bold=True,italic=True)
line('segment-boundary1',1096,98,1096,228,'#CC3388',3,dash=True);line('segment-boundary2',1208,98,1208,228,'#CC3388',3,dash=True)
for i,x in enumerate([988,1148,1318]):line('policy-down'+str(i),x,229,x,279,arrow=True)
text('learn-robot','learn robot policies',1044,233,209,30,21,'#E94A2C',italic=True)
# Native editable wireframe CNN mini-diagrams, drawn to the source layout.
def net(prefix,x,y):
 color='#9AB7C8'
 for j,(dx,dy,w,h) in enumerate([(0,0,23,51),(28,10,15,32),(47,15,13,22),(68,20,13,15),(94,19,14,20),(122,22,13,13),(158,10,4,40)]):
  pts=[(x+dx,y+dy+6),(x+dx+7,y+dy),(x+dx+w+7,y+dy+3),(x+dx+w+7,y+dy+h-3),(x+dx+w,y+dy+h+3),(x+dx,y+dy+h)]
  commands=[{'moveTo':dict(x=pts[0][0],y=pts[0][1])}]+[{'lineTo':dict(x=a,y=b)} for a,b in pts[1:]]+[{'close':{}}];path(prefix+'box'+str(j),commands,color,.75)
  line(prefix+'inner'+str(j),x+dx+7,y+dy,x+dx+7,y+dy+h-3,color,.65)
  if j<6:line(prefix+'conn'+str(j),x+dx+w,y+dy+h/2,x+[28,47,68,94,122,158][j],y+28,color,.65)
  if j==6:
   for k in range(1,9):line(prefix+'unit'+str(k),x+dx,y+dy+k*4,x+dx+w+7,y+dy+k*4,color,.6)
for i,x in enumerate([877,1065,1253]):net('net'+str(i),x,284)
curve('policy-next1',997,340,1030,367,1070,368,1112,335,'#287BBE',2);curve('policy-next2',1180,340,1216,367,1250,369,1290,335,'#287BBE',2)
text('advance','advance robot policy w/',944,357,265,30,20,'#666666');text('predictor-robot','phase predictor φᵣ',1197,357,226,30,20,'#347C28',bold=True,italic=True)
text('metatime','meta-training time',725,379,176,26,22,'#333333',rotation=-90);text('testtime','meta-test time',786,407,128,26,22,'#333333',rotation=-90)
curve('train-test',788,510,813,541,842,540,868,507)
d=dict(schema_version=1,id='one-shot-hierarchical-figure-2',title=s['title_expected']+' — Figure 2',canvas=dict(width=1434,height=540),provenance=dict(paper_title=s['title_expected'],paper_url=s['source_url'],figure='Figure 2',page=3,license=s['license_note'],status='figure_recreation',source_sha256=s['pdf_sha256'],source_crop_pdf_points=[66,48,544,224],notes='Manual faithful-layout reconstruction from a flattened source figure. All ordinary labels, phase arrows, dividers and three network mini-diagrams are native. Twenty individual video frames and the compact meta-learning objective remain raster. Network wireframes, fonts, shadows and curved arrows approximate source; freeform edges are not semantically attached. Bottom margin expanded by 12 pixels to retain the curved transition arrow.'),nodes=nodes,edges=[])
(out/'one-shot-hierarchical-figure-2.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
