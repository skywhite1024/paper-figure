"""Manual native reconstruction of the inspected RoboSegNet architecture."""
import json,math,fitz
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];cid='learning-multi-task-robot-trajectory-segmentation-from-visual-and-kinematic-streams-robosegnet';s=json.loads((ROOT/'research/survey'/f'{cid}.json').read_text());out=ROOT/'data/diagrams/robosegnet';out.mkdir(parents=True,exist_ok=True);page=fitz.open(ROOT/s['pdf_path'])[3];page.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(62,73,549,243)).save(out/'robosegnet-figure-2-original.png');im=Image.open(out/'robosegnet-figure-2-original.png');N=[]
def box(id,x,y,w,h,fill='#FFFFFF',stroke='#666666',width=1,rounded=False,label='',size=13):N.append(dict(id=id,shape='rounded_rect' if rounded else 'rect',x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=width,label=label,font_family='Arial',font_size=size,text_color='#55565D',align='center',text_inset=0,no_wrap=True))
def text(id,label,x,y,w,h=22,size=15,color='#666A71',bold=False):N.append(dict(id=id,shape='text',label=label,x=x,y=y,width=w,height=h,font_family='Arial',font_size=size,text_color=color,bold=bold,align='center',no_wrap=True,text_inset=0))
def path(id,pts,color='#61656B',width=1.3,fill='none',close=False):N.append(dict(id=id,shape='path',x=0,y=0,width=974,height=340,commands=[{'moveTo':dict(x=pts[0][0],y=pts[0][1])}]+[{'lineTo':dict(x=x,y=y)} for x,y in pts[1:]]+([{'close':{}}] if close else []),fill=fill,stroke=color,stroke_width=width))
def arrow(id,pts,color='#61656B',width=1.8,head=7):
 path(id,pts,color,width);(a,b),(x,y)=pts[-2:];ang=math.atan2(y-b,x-a);path(id+'head',[(x-head*math.cos(ang-.48),y-head*math.sin(ang-.48)),(x,y),(x-head*math.cos(ang+.48),y-head*math.sin(ang+.48))],color,width)
for i,r in enumerate([(15,41,110,121),(131,41,226,121),(249,41,344,121),(421,36,545,129),(580,36,705,129)]):
 name=f'source-inset-{i}.png';im.crop(r).save(out/name);N.append(dict(id='image'+str(i),shape='image',asset=name,alt='Original kinematic plot with internal labels' if i<3 else 'Original robot observation with patch grid',x=r[0],y=r[1],width=r[2]-r[0],height=r[3]-r[1]))
text('kinematic','Kinematic stream',75,3,215,27,20,'#85858E');text('image-stream','Image stream',473,1,171,27,20,'#85858E');text('transitions','Predicted Transitions',775,1,190,28,20,'#85858E')
for id,x in [('kin1',111),('kin2',230),('imgs',552)]:text(id,'...',x,62,19,29,18)
arrow('kin-input',[(172,125),(172,149)])
box('dct-container',7,154,331,178,'#FFFFFF','#111111',2.4,True)
box('dct-chart',34,162,275,136,'#FFFFFF','#A6A6A6',.6)
text('dct-title','Discrete Cosine Transform',80,162,180,18,11,'#55565D')
arrow('dct-x',[(43,253),(298,253)],width=1,head=5);arrow('dct-y',[(43,253),(43,178)],width=1,head=5)
for i,(x,h,c) in enumerate([(64,34,'#E5CECE'),(81,31,'#ABC4C4'),(96,43,'#AE98B0'),(125,62,'#E5CECE'),(141,34,'#ABC4C4'),(157,20,'#AE98B0'),(184,32,'#E5CECE'),(200,42,'#ABC4C4'),(216,33,'#AE98B0'),(244,31,'#E5CECE'),(260,25,'#ABC4C4'),(276,62,'#AE98B0')]):box('bar'+str(i),x,247-h,11,h,c,'none',0,True)
for i,x in enumerate([51,114,177,240]):
 box('wave-box'+str(i),x,259,55,31,'#FFFFFF','#111111',1.2,True)
 pts=[(x+4+t*47/80,274+8*math.sin(t/80*math.pi*2*([1,2,3,5][i]))) for t in range(81)];path('wave'+str(i),pts,'#BDBD68',.7)
for id,label,x,w in [('quantize','Quantize',33,63),('flatten','Flatten',101,54),('bytepair','Byte Pair Encoding',160,106)]:box(id,x,302,w,21,'#F1F1F1','none',0,label=label,size=10)
text('fast','FAST',273,298,58,33,25,'#778F98')
for i,y in enumerate([207,238,268,299]):box('kin-token'+str(i),365,y,24,25,'#7D677F','none',0)
arrow('kin-tokens',[(342,265),(361,265)]);arrow('tokens-attn',[(393,265),(409,265)])
for i,x in enumerate([420,451,482,513,579,610,641,672]):box('image-token'+str(i),x,162,24,23,'#C8DDD1' if i<4 else '#9DBDAB','none',0)
text('dino1','DINOv3',397,130,85,31,23,'#7A929B');text('dino2','DINOv3',642,130,85,31,23,'#7A929B');arrow('dino-down1',[(484,133),(484,155)]);arrow('dino-down2',[(638,133),(638,155)])
box('sum-image',545,163,20,20,'#FFFFFF','#111111',2,True,label='+',size=26);arrow('sum-down',[(555,184),(555,204)])
box('attention',412,209,296,123,'#EBEBEB','#111111',2.4,True)
text('attention-title','Bi-directional Cross attention',429,215,261,28,16,'#55565D',True)
for i,x in enumerate([428,454,480,506]):box('attention-purple-top'+str(i),x,252,20,20,'#7D677F','none',0)
for i,x in enumerate([564,586,608,630,652,674]):box('attention-green-top'+str(i),x,250,20,20,'#CDDCD3' if i<3 else '#9DBCAA','none',0)
for i,(x,w) in enumerate([(429,33),(464,20),(486,20),(508,20),(530,20)]):box('attention-green-bottom'+str(i),x,303,w,19,'#CADDD0' if i>1 else '#9DBCAA','none',0)
for i,x in enumerate([586,612,638,664]):box('attention-purple-bottom'+str(i),x,302,20,20,'#7D677F','none',0)
def biarrow(id,start,end):
 path(id,[start,end],width=1.1)
 for suffix,(a,b),(x,y) in [('end',start,end),('start',end,start)]:
  angle=math.atan2(y-b,x-a);L=5;W=2.1
  path(id+suffix,[(x,y),(x-L*math.cos(angle)+W*math.sin(angle),y-L*math.sin(angle)-W*math.cos(angle)),(x-L*math.cos(angle)-W*math.sin(angle),y-L*math.sin(angle)+W*math.cos(angle))],'none',0,'#61656B',True)
for i,x in enumerate([435,469,497,518,541]):biarrow('cross-left'+str(i),(517,274),(x,303))
for i,x in enumerate([592,618,644,670]):biarrow('cross-right'+str(i),(566,274),(x,301))
arrow('attention-out',[(711,265),(729,265)])
for i,y in enumerate([215,247,278,309]):box('encoded'+str(i),733,y,23,24,'#A4C1C9','none',0)
box('pe-bg',733,158,23,23,'#D0DCE8','none',0,label='PE',size=20)
box('sum-pe',734,188,20,20,'#FFFFFF','#111111',2,True,label='+',size=26)
arrow('encoder-route',[(756,198),(771,198),(771,302),(792,302)])
box('trajectory',795,279,167,54,'#E6E0E9','#6A526D',2.3,True,label='Trajectory Encoder',size=16)
box('boundary',795,198,167,54,'#F5ECEC','#946B6B',2.3,True,label='Boundary Decoder',size=16)
box('prediction',795,99,168,54,'#E2E6ED','#87909D',2.3,True,label='Prediction Head',size=16)
arrow('trajectory-boundary',[(875,277),(875,256)])
colors=['#ED9A35','#F5EC1F','#478DEE','#3D8F56']
for i,(x,c) in enumerate(zip([806,843,883,925],colors)):
 box('boundary-token'+str(i),x,159,22,22,c,'none',0);arrow('boundary-up'+str(i),[(x+11,197),(x+11,183)]);arrow('prediction-up'+str(i),[(x+11,98),(x+11,81)]);text('transition-label'+str(i),'t,p(t)',x-7,66,37,20,11,c)
box('timeline-bg-green',797,34,55,20,'#CDDDD4','none',0);box('timeline-bg-blue',852,34,50,20,'#C3CFDF','none',0);box('timeline-bg-pink',902,34,48,20,'#E8CECE','none',0);path('timeline',[(797,47),(950,47)],'#000000',5);path('timeline-head',[(955,47),(939,39),(939,55)],'none',0,'#000000',True);path('timeline-start',[(797,37),(797,57)],'#000000',5)
for id,x,c in [('orange',852,'#ED9A35'),('blue',902,'#478DEE')]:path('transition-'+id,[(x,32),(x-10,51),(x+10,51)],'none',0,c,True)
arrow('orange-transition-route',[(817,66),(848,50)],width=2.5);arrow('blue-transition-route',[(898,65),(901,51)],width=2.5)
for n in list(N):
 if n['id'] in ['sum-image','sum-pe']:n['shape']='ellipse'
 if n['id']=='dct-chart':n['dash']=True
 if n['id'] in ['dct-container','attention','trajectory','boundary','prediction'] or n['id'].startswith('wave-box'):
  w,h=n['width'],n['height'];r=12 if n['id'].startswith('wave-box') else 18;k=.55228475
  if n.get('label'):text(n['id']+'-label',n['label'],n['x'],n['y']+h/2-12,w,24,n['font_size'],'#55565D',True)
  n['label']='';n['shape']='path';n['commands']=[{'moveTo':dict(x=r,y=0)},{'lineTo':dict(x=w-r,y=0)},{'cubicBezTo':dict(x1=w-r+k*r,y1=0,x2=w,y2=r-k*r,x=w,y=r)},{'lineTo':dict(x=w,y=h-r)},{'cubicBezTo':dict(x1=w,y1=h-r+k*r,x2=w-r+k*r,y2=h,x=w-r,y=h)},{'lineTo':dict(x=r,y=h)},{'cubicBezTo':dict(x1=r-k*r,y1=h,x2=0,y2=h-r+k*r,x=0,y=h-r)},{'lineTo':dict(x=0,y=r)},{'cubicBezTo':dict(x1=0,y1=r-k*r,x2=r-k*r,y2=0,x=r,y=0)},{'close':{}}]
d=dict(schema_version=1,id='robosegnet-figure-2',title=s['title_expected']+' — Figure 2',canvas=dict(width=974,height=340),provenance=dict(paper_title=s['title_expected'],paper_url=s['source_url'],figure='Figure 2',page=4,license=s['license_note'],status='figure_recreation',source_sha256=s['pdf_sha256'],source_crop_pdf_points=[62,73,549,243],notes='Manual source-layout reconstruction of the flattened architecture. All major labels, modules, DCT bars/wave schematics, token tiles, cross-attention links and prediction routes are native. Three kinematic chart crops with internal tiny labels and two observation patch-grid crops remain raster. Colors and topology retained; exact source fonts, shadow blur, waveform traces and small transition-label typography are approximated. Native freeform routes lack semantic attachment.'),nodes=N,edges=[])
(out/'robosegnet-figure-2.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
