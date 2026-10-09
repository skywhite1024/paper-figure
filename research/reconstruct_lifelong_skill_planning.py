"""Rebuild inspected raster skill-planning schematic as native shapes/text."""
import json,math,fitz
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];cid='reset-free-lifelong-learning-with-skill-space-planning';s=json.loads((ROOT/'research/survey'/f'{cid}.json').read_text());out=ROOT/'data/diagrams/lifelong-skill-planning';out.mkdir(parents=True,exist_ok=True);nodes=[]
def box(id,label,x,y,w,h,fill='#FFFFFF',stroke='#666666',rounded=False,dash=False,size=15,bold=True):nodes.append(dict(id=id,shape='rounded_rect' if rounded else 'rect',label=label,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=1.8,dash=dash,font_family='Arial',font_size=size,bold=bold,text_color='#000000',align='center',text_inset=0,no_wrap=True))
def txt(id,label,x,y,w,h=22,size=16,bold=False):nodes.append(dict(id=id,shape='text',label=label,x=x,y=y,width=w,height=h,font_family='Arial',font_size=size,bold=bold,text_color='#000000',align='center',no_wrap=True,text_inset=0))
def path(id,cmd,stroke='#777777',width=1.8,fill='none'):nodes.append(dict(id=id,shape='path',x=0,y=0,width=1197,height=133,commands=cmd,stroke=stroke,stroke_width=width,fill=fill))
def arrow(id,x1,y1,x2,y2,color):
 path(id,[{'moveTo':dict(x=x1,y=y1)},{'lineTo':dict(x=x2,y=y2)}],color,2.5);a=math.atan2(y2-y1,x2-x1);L=13;W=5
 path(id+'-head',[{'moveTo':dict(x=x2,y=y2)},{'lineTo':dict(x=x2-L*math.cos(a)+W*math.sin(a),y=y2-L*math.sin(a)-W*math.cos(a))},{'lineTo':dict(x=x2-L*math.cos(a)-W*math.sin(a),y=y2-L*math.sin(a)+W*math.cos(a))},{'close':{}}],'none',0,color)
box('discriminator','',9,6,245,32,'#B49FC5');box('distribution','',9,48,245,32,'#E98A89')
box('algorithm2','',330,6,233,116,stroke='#999999',rounded=True,dash=True)
for i,line in enumerate(['Algorithm 2','Generate synthetic','rollouts for training','Train policy on intrinsic','rewards using rollouts']):txt('algo2-'+str(i),line,337,16+i*19,219,22,19 if i==0 else 15.5,True)
box('dynamics','',637,6,245,32,'#9CD8E5');box('policy','',637,48,245,32,'#F6A079')
box('algorithm3','',957,6,232,74,stroke='#999999',rounded=True,dash=True)
for i,line in enumerate(['Algorithm 3','Plan in skill space to act in','the environment']):txt('algo3-'+str(i),line,963,16+i*19,220,22,19 if i==0 else 15.5,True)
for id,x1,y1,x2,y2,color in [('disc-out',271,12,314,12,'#9873B9'),('disc-in',314,31,271,31,'#9873B9'),('practice-out',271,54,314,54,'#EC5964'),('practice-in',314,73,271,73,'#EC5964'),('dynamics-algo',621,13,577,13,'#77C9DC'),('policy-algo',621,54,577,54,'#FB845F'),('algo-policy',578,73,621,73,'#FB845F'),('dynamics-planner',898,13,941,13,'#77C9DC'),('planner-dynamics',941,32,898,32,'#77C9DC'),('policy-planner',898,55,941,55,'#FB845F')]:arrow(id,x1,y1,x2,y2,color)
txt('legend1','incoming arrow denotes',48,88,172,17,14);txt('legend2','training from data',63,105,153,17,14)
path('legend-bend',[{'moveTo':dict(x=294,y=84)},{'lineTo':dict(x=294,y=106)},{'lineTo':dict(x=225,y=106)}]);path('legend-head',[{'moveTo':dict(x=223,y=106)},{'lineTo':dict(x=232,y=102)},{'lineTo':dict(x=232,y=110)},{'close':{}}],'none',0,'#777777')
# Source q_psi, p_psi, f_phi and pi_theta are distinct, typeable native labels.
for id,label,x,y,w in [('disc-title','Skill Discriminator',51,12,142),('dist-title','Skill-Practice Distribution',24,54,197),('dyn-title','Dynamics Model Ensemble',649,12,194),('pol-title','Skill Policy',712,54,77)]:txt(id,label,x,y,w,22,15,True)
for id,label,x,y in [('disc-q','q',193,12),('dist-p','p',223,54),('dyn-f','f',844,12),('pol-pi','π',789,54)]:txt(id,label,x,y,13,22,16,True)
for id,label,x,y in [('disc-psi','ψ',204,23),('dist-psi','ψ',234,65),('dyn-phi','φ',854,23),('pol-theta','θ',802,65)]:txt(id,label,x,y,12,14,10,True)
d=dict(schema_version=1,id='lifelong-skill-planning-figure-2',title=s['title_expected']+' — Figure 2',canvas=dict(width=1197,height=133),provenance=dict(paper_title=s['title_expected'],paper_url=s['source_url'],figure='Figure 2',page=5,license=s['license_note'],status='figure_recreation',source_sha256=s['pdf_sha256'],source_crop_pdf_points=[106,81,505,124],notes='Original compact algorithm schematic manually reconstructed from one flattened raster. All text, colored modules, algorithm containers and arrows are native. Fonts, math-subscript placement, dash cadence and corner radii approximate the original. Arrows are freeform paths, not semantically attached connectors. No raster backdrop or image objects.'),nodes=nodes,edges=[])
(out/'lifelong-skill-planning-figure-2.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');fitz.open(ROOT/s['pdf_path'])[4].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(106,81,505,124)).save(out/'lifelong-skill-planning-figure-2-original.png')
