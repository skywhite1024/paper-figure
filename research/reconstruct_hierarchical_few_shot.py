"""Reconstruct source Figure 2 topology and labels as native editable objects."""
import json,math,fitz
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];cid='hierarchical-few-shot-imitation-with-skill-transition-models';s=json.loads((ROOT/'research/survey'/f'{cid}.json').read_text());out=ROOT/'data/diagrams/hierarchical-few-shot';out.mkdir(parents=True,exist_ok=True);N=[]
def text(id,label,x,y,w,h=24,size=15,color='#111111',bold=False,font='Arial'):
 N.append(dict(id=id,shape='text',label=label,x=x,y=y,width=w,height=h,font_family=font,font_size=size,text_color=color,bold=bold,align='center',no_wrap=True,text_inset=0))
def shape(id,kind,x,y,w,h,fill,stroke,width=1,label='',size=14):N.append(dict(id=id,shape=kind,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=width,label=label,font_family='Arial',font_size=size,text_color='#111111',align='center',text_inset=0,no_wrap=True))
def path(id,cmd,stroke='#437ED8',width=1.5,fill='none',dash=False):N.append(dict(id=id,shape='path',x=0,y=0,width=1017,height=429,commands=cmd,fill=fill,stroke=stroke,stroke_width=width,dash=dash))
def poly(id,pts,stroke='#437ED8',width=1.5,fill='none',close=False,dash=False):path(id,[{'moveTo':dict(x=pts[0][0],y=pts[0][1])}]+[{'lineTo':dict(x=x,y=y)} for x,y in pts[1:]]+([{'close':{}}] if close else []),stroke,width,fill,dash)
def rr(id,x,y,w,h,r,fill,stroke,width=1,dash=False):
 k=.55228475;path(id,[{'moveTo':dict(x=x+r,y=y)},{'lineTo':dict(x=x+w-r,y=y)},{'cubicBezTo':dict(x1=x+w-r+k*r,y1=y,x2=x+w,y2=y+r-k*r,x=x+w,y=y+r)},{'lineTo':dict(x=x+w,y=y+h-r)},{'cubicBezTo':dict(x1=x+w,y1=y+h-r+k*r,x2=x+w-r+k*r,y2=y+h,x=x+w-r,y=y+h)},{'lineTo':dict(x=x+r,y=y+h)},{'cubicBezTo':dict(x1=x+r-k*r,y1=y+h,x2=x,y2=y+h-r+k*r,x=x,y=y+h-r)},{'lineTo':dict(x=x,y=y+r)},{'cubicBezTo':dict(x1=x,y1=y+r-k*r,x2=x+r-k*r,y2=y,x=x+r,y=y)},{'close':{}}],stroke,width,fill,dash)
def arrow(id,pts,color='#437ED8',width=1.5,dash=False):
 poly(id,pts,color,width,dash=dash);(x1,y1),(x2,y2)=pts[-2:];a=math.atan2(y2-y1,x2-x1);ln=6;wd=3
 poly(id+'-head',[(x2,y2),(x2-ln*math.cos(a)+wd*math.sin(a),y2-ln*math.sin(a)-wd*math.cos(a)),(x2-ln*math.cos(a)-wd*math.sin(a),y2-ln*math.sin(a)+wd*math.cos(a))],'none',0,color,True)
def cylinder(id,x,y,w,h,fill,stroke):
 # Body and cap stay separate editable paths/shapes.
 path(id+'body',[{'moveTo':dict(x=x,y=y+10)},{'lineTo':dict(x=x,y=y+h-10)},{'cubicBezTo':dict(x1=x,y1=y+h+3,x2=x+w,y2=y+h+3,x=x+w,y=y+h-10)},{'lineTo':dict(x=x+w,y=y+10)},{'close':{}}],stroke,1,fill)
 shape(id+'cap','ellipse',x,y,w,20,fill,stroke)
def dot(id,x,y,r=3,color='#477ED6'):shape(id,'ellipse',x-r,y-r,r*2,r*2,color,'none')
rr('left-panel',7,8,683,416,43,'#F6F0E2','#D6AF63');rr('right-panel',701,8,310,416,28,'#F6F0E2','#D6AF63');rr('adapt-panel',193,21,205,152,27,'#FAEBBE','#E9B316')
text('extraction','(a) Skill Extraction',32,27,152,27,15,bold=True);text('adaptation','(b) Skill Adaptation',204,27,173,27,15,bold=True);text('few-shot-title','(c) Few-Shot Imitation',723,27,193,27,15,bold=True)
cylinder('dataset',73,68,111,80,'#FFD2AE','#DB783C');text('unlabelled','Un-labeled',76,94,105,23,14,'#BD5C15',True);text('offline','offline dataset',75,114,106,23,14,'#BD5C15',True)
cylinder('demos',255,68,111,80,'#DEC4D2','#AF65D6');text('few-shot','Few-shot',259,94,103,23,14,'#9636DC',True);text('demos-label','demos',259,114,103,23,14,'#9636DC',True)
poly('plus',[(216,89),(228,89),(228,106),(245,106),(245,117),(228,117),(228,134),(216,134),(216,117),(199,117),(199,106),(216,106)],'#AF6AD6',1,'#DFC0DE',True)
rr('decoder-frame',430,21,225,396,36,'none','#111111',2,dash=True);rr('encoder-frame',43,247,374,70,11,'none','#F27736',2,dash=True);rr('decoder-mlp-frame',445,68,175,70,10,'none','#F27736',2,dash=True);rr('inverse-frame',455,247,157,70,10,'none','#F27736',2,dash=True)
text('encoder-title','Skill Encoder',45,219,117,26,14,'#666666',True);text('decoder-title','Skill Decoder',551,41,97,24,14,'#666666',True)
for i,x in enumerate([53,164,326]):shape('lstm'+str(i),'rect',x,257,79,49,'#ACCAE7','#7EA2C7',.6,'LSTM',12)
arrow('lstm-link1',[(132,281),(164,281)],'#AEC8E8',1);arrow('lstm-link2',[(295,281),(326,281)],'#AEC8E8',1)
for i,x in enumerate([257,269,281]):dot('lstm-dot'+str(i),x,282)
for i,(x,label) in enumerate([(68,'S₁'),(118,'a₁'),(179,'S₂'),(229,'a₂'),(343,'Sₕ'),(393,'aₕ')]):
 shape('input'+str(i),'ellipse',x-15,330,30,30,'#D9E3F5','#6097E1',1);text('input-label'+str(i),label,x-14,331,28,29,16,'#427ADD');arrow('input-arrow'+str(i),[(x,330),(x,306)])
for i,x in enumerate([274,286,298]):dot('input-dot'+str(i),x,344,4)
arrow('encode-skill',[(366,257),(366,195),(491,195)])
shape('skill','rect',491,183,79,25,'#C6DE9B','#97B779',.8);text('skill-label','Skill (z)',492,183,77,25,14,'#567133',True)
poly('inverse-mlp',[(477,257),(584,257),(596,306),(466,306)],'#FF4444',1,'#EBCFC5',True);text('inverse-mlp-label','MLP',488,268,89,28,16,'#FF2222')
for i,(x,label) in enumerate([(503,'S₁'),(553,'Sₕ')]):shape('inverse-input'+str(i),'ellipse',x-15,330,30,30,'#D9E3F5','#6097E1',1);text('inverse-input-label'+str(i),label,x-14,331,28,29,16,'#427ADD');arrow('inverse-input-arrow'+str(i),[(x,330),(x,306)])
arrow('inverse-skill',[(531,257),(531,208)]);text('inverse-title','Inverse Skill Dynamics',464,371,180,26,14,'#666666',True);text('inverse-formula',"q(z | s, s′)",481,392,137,23,18,'#666666',True,'Times New Roman')
shape('decoder-mlp','rect',455,77,153,49,'#FFDA8D','#DAB15E',.6);text('mlp-label','MLP',479,89,105,24,12,'#7C4B12');arrow('skill-decoder',[(531,183),(531,126)]);shape('decoder-state','ellipse',544,147,31,31,'#D9E3F5','#6097E1',1);text('decoder-state-label','Sₜ',544,147,31,31,17,'#427ADD');arrow('state-decoder',[(560,147),(560,126)]);shape('action','ellipse',516,24,29,30,'#D9E3F5','#6097E1',1);text('action-label','aₜ',516,24,31,31,16,'#427ADD');arrow('decoder-action',[(531,77),(531,54)])
text('trajectories','Few-shot\ntrajectories',706,74,94,45,14,'#9739D8',True)
path('trajectory',[{'moveTo':dict(x=758,y=154)},{'cubicBezTo':dict(x1=800,y1=93,x2=817,y2=74,x=857,y=128)},{'cubicBezTo':dict(x1=899,y1=183,x2=908,y2=238,x=988,y=117)},{'cubicBezTo':dict(x1=1003,y1=169,x2=884,y2=263,x=814,y=213)},{'lineTo':dict(x=758,y=154)}],'#983ADD',2)
text('tau1','τ₁',744,116,37,23,17,'#983ADD',font='Times New Roman');text('tau2','τ₂',747,161,37,23,17,'#983ADD',font='Times New Roman')
def star(id,cx,cy,color):
 pts=[]
 for j in range(10):a=-math.pi/2+j*math.pi/5;r=15 if j%2==0 else 5;pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 poly(id,pts,'none',0,color,True)
star('start-star',815,212,'#078DCC');star('goal-star',895,217,'#00B765')
for id,cx,cy,col in [('start',769,292,'#078DCC'),('target',840,254,'#00B765')]:poly(id+'x1',[(cx-9,cy-9),(cx+9,cy+9)],col,4);poly(id+'x2',[(cx-9,cy+9),(cx+9,cy-9)],col,4)
arrow('blue-min',[(814,219),(770,286)],'#078DCC',2,dash=True);arrow('green-min',[(775,290),(838,258)],'#00B765',2,dash=True);arrow('h-steps',[(831,210),(879,216)],'#00B765',2,dash=True)
text('h-label','H steps',829,186,57,24,14,'#00B765',True);text('min-distance','min d(s₁, s*)',704,223,113,27,16,'#078DCC',font='Times New Roman');text('min-s','s*',710,238,25,19,13,'#078DCC',font='Times New Roman');text('s1','s₁',743,294,28,24,18,'#078DCC',font='Times New Roman');text('goal-label','s*ₕ',894,225,29,24,18,'#00B765',font='Times New Roman')
text('policy-formula','a∼π(a | s₁,z) q(z | s₁,s*ₕ)',785,270,199,29,18,font='Times New Roman');arrow('decode-to-policy',[(655,366),(880,366),(880,297)],'#111111',2,dash=True)
# Unicode lacks uppercase subscript H; use separate typeable native H objects.
for n in list(N):
 if n['id'] in ['input-label4','input-label5','inverse-input-label1','goal-label']:
  n['label']=n['label'].replace('ₕ','')
  text(n['id']+'-H','H',n['x']+19,n['y']+15,13,14,10,n['text_color'])
 if n['id']=='policy-formula':n['label']='a∼π(a | s₁,z) q(z | s₁,s*_H)';n['font_size']=17
 if n['id']=='inverse-formula':n['italic']=True
from math_glyph import glyph_node
N=[n for n in N if n['id']!='policy-formula']
N.append(glyph_node('policy-formula',r'a\sim\pi(a\mid s_1,z)\,q(z\mid s_1,s_H^{*})',790,278,177,20))
d=dict(schema_version=1,id='hierarchical-few-shot-figure-2',title=s['title_expected']+' — Figure 2',canvas=dict(width=1017,height=429),provenance=dict(paper_title=s['title_expected'],paper_url=s['source_url'],figure='Figure 2',page=4,license=s['license_note'],status='figure_recreation',source_sha256=s['pdf_sha256'],source_crop_pdf_points=[131,105,470,248],notes='Manual reconstruction of all three panels from a flattened source figure. All labels, mathematical notation, modules, arrows, trajectory curves and markers are native editable objects, with no raster assets. Source gradients replaced by close flat fills; font/subscript typography, curve control points and line/dash widths are approximated. Most mathematical labels are typeable text; the compact policy formula uses editable STIX glyph outlines with its LaTeX transcription retained, not a live equation field. Freeform routes are not semantically attached.'),nodes=N,edges=[])
(out/'hierarchical-few-shot-figure-2.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');fitz.open(ROOT/s['pdf_path'])[3].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(131,105,470,248)).save(out/'hierarchical-few-shot-figure-2-original.png')
