"""Source-measured native reconstruction of LGSD, Scaling Up and SDS raster figures."""
import argparse,json,sys,hashlib,math,subprocess
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from paper_figure.model import validate
p=argparse.ArgumentParser();p.add_argument('slug',choices=['lgsd','scaling-up','sds']);a=p.parse_args();slug=a.slug
index,pg,fig,crop,scale={'lgsd':(51,4,'Figure 2',[113,78,492,217],3),'scaling-up':(55,5,'Figure 4',[305,535,505,626],6),'sds':(128,3,'Figure 2',[108,311,505,509],3)}[slug]
catalog=json.load(open(R/'data/catalog.json'))['papers'];m=json.load(open(R/'research/survey'/(catalog[index]['id']+'.json')));pdf=R/m['pdf_path'];doc=fitz.open(pdf);page=doc[pg-1];D=R/'data/diagrams'/slug;D.mkdir(parents=True,exist_ok=True);page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=fitz.Rect(crop)).save(D/'original.png');im=Image.open(D/'original.png');W,H=im.size
s={'schema_version':1,'id':slug+'-figure-'+fig.split()[-1],'title':m['title_expected']+' · '+fig,'canvas':{'width':W,'height':H},'provenance':{'paper_title':m['title_expected'],'paper_url':m['source_url'],'figure':fig,'page':pg,'license':m.get('license_note','unverified'),'notes':'Native source-layout reconstruction of flattened original. Ordinary labels and code are typeable. Diagram shapes and logical arrows are native. Explicitly bounded source photographs, icons and mathematical formula inserts retain raster pixels. Font metrics and path coordinates are measured approximations.','status':'figure_recreation','source_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'source_crop_pdf_points':crop,'raster_details':[]},'nodes':[],'edges':[]}
def node(id,shape,x,y,w,h,**kw):
 n=dict(id=id,shape=shape,x=x,y=y,width=max(.01,w),height=max(.01,h),fill='none',stroke='none');n.update(kw);s['nodes'].append(n);return n
def text(id,label,x,y,w,h,fs=22,color='#000000',bold=False,italic=False,font='Arial',align='center',rotation=0):return node(id,'text',x,y,w,h,label=label,font_size=fs,font_family=font,text_color=color,bold=bold,italic=italic,align=align,text_inset=0,no_wrap=True,rotation=rotation)
def rect(id,x,y,w,h,fill='none',stroke='#000000',sw=2,rounded=False,**kw):return node(id,'rounded_rect'if rounded else'rect',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,**kw)
def ellipse(id,x,y,w,h,fill='none',stroke='#000000',sw=2):return node(id,'ellipse',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw)
def path(id,cmds,stroke='#000000',sw=2,fill='none',dash=False):
 pts=[(v[k],v['y'+k[1:]])for cmd in cmds for op,v in cmd.items()for k in ['x','x1','x2']if k in v];x=min(p[0]for p in pts);y=min(p[1]for p in pts);w=max(p[0]for p in pts)-x;h=max(p[1]for p in pts)-y;cc=[]
 for c in cmds:
  op,v=next(iter(c.items()));v=dict(v)
  for k in ['x','x1','x2']:
   if k in v:v[k]-=x;v['y'+k[1:]]-=y
  cc.append({op:v})
 return node(id,'path',x,y,w,h,commands=cc,stroke=stroke,stroke_width=sw,fill=fill,dash=dash)
def poly(id,pts,stroke='#000000',sw=2,fill='none',close=False,dash=False):return path(id,[{('moveTo'if j==0 else'lineTo'):{'x':x,'y':y}}for j,(x,y)in enumerate(pts)]+([{'close':{}}]if close else[]),stroke,sw,fill,dash)
def tip(id,end,prev,color='#000000',size=10,open=False):
 dx=end[0]-prev[0];dy=end[1]-prev[1];l=math.hypot(dx,dy);ux,uy=dx/l,dy/l;b=(end[0]-size*ux,end[1]-size*uy);p1=(b[0]-size*.45*uy,b[1]+size*.45*ux);p2=(b[0]+size*.45*uy,b[1]-size*.45*ux);poly(id,[p1,end,p2],color,1.6 if open else 0,'none'if open else color,not open)
def line(id,pts,color='#000000',sw=2,arrow=False,dash=False,head=False,size=10):
 n=poly(id,pts,color,sw,dash=dash)
 if arrow:tip(id+'-tip',pts[-1],pts[-2],color,size)
 if head:tip(id+'-head',pts[0],pts[1],color,size)
 return n
def curve(id,start,c1,c2,end,color='#000000',sw=2,arrow=False,open=False,size=10):
 n=path(id,[{'moveTo':dict(zip(('x','y'),start))},{'cubicBezTo':{'x1':c1[0],'y1':c1[1],'x2':c2[0],'y2':c2[1],'x':end[0],'y':end[1]}}],color,sw)
 if arrow:tip(id+'-tip',end,c2,color,size,open)
 return n
def image(id,box,alt):
 x,y,x1,y1=box;name=id+'.png';piece=im.crop(box).convert('RGBA')
 if id in ['language-near-formula','language-far-formula']:
  import numpy as np
  pixels=np.array(piece);yy,xx=np.indices(pixels.shape[:2]);remove=yy>=(18 if id=='language-far-formula' else 19+.31*xx);pixels[remove,3]=0;piece=Image.fromarray(pixels)
 piece.save(D/name);node(id,'image',x,y,x1-x,y1-y,asset=name,alt=alt);s['provenance']['raster_details'].append({'id':id,'source_pixels':box,'detail':alt})
if slug=='lgsd':
 poly('state-plane',[(12,328),(218,97),(545,97),(337,329)],'#777777',1,'none',True);ellipse('latent-space',762,101,357,250,sw=1.8)
 text('state-label','State space',240,32,144,31,26);text('latent-label','Latent space',869,34,151,32,26)
 for id,box in [('robot-state-s',(207,181,260,233)),('robot-state-sp',(365,114,418,168))]:image(id,box,'Individual original quadruped illustration')
 ellipse('origin-point',123,263,9,9,'#FFFFFF','#555555',1);ellipse('latent-s-point',876,241,9,9,'#FFFFFF','#555555',1);ellipse('latent-sp-point',969,153,9,9,'#FFFFFF','#555555',1)
 curve('origin-to-s',(136,261),(145,235),(179,221),(206,218),'#555555',1.8,True,True,15);curve('s-to-sp',(260,188),(296,165),(320,151),(360,157),'#555555',1.8,True,True,14);curve('phi-map',(562,82),(608,38),(721,56),(773,85),'#555555',1.6,True,True,14)
 line('latent-displacement',[(889,237),(965,164)],'#555555',1.3);tip('latent-displacement-head',(965,164),(889,237),'#555555',10,True)
 line('latent-prior-vector',[(910,245),(997,230)],'#6EA4DC',1.6);tip('latent-prior-head',(997,230),(910,245),'#6EA4DC',10,True)
 line('llm-near-route',[(240,251),(408,305)],'#555555',1.7,True,True,size=8);line('llm-far-route',[(390,182),(534,184)],'#555555',1.7,True,True,size=8);line('language-distance',[(515,294),(601,216)],'#555555',1.7,True,True,True,size=8)
 text('origin','origin',82,278,81,28,26,italic=True,font='Times New Roman');text('state-s','s',213,233,26,23,23,italic=True,font='Times New Roman');text('state-sp','s′',366,168,27,24,23,italic=True,font='Times New Roman')
 text('far-description','"Robot is far\nfrom the origin"',538,164,200,42,19,bold=True,font='Courier New',align='left');text('near-description','"Robot is near\nthe origin"',410,306,199,42,19,bold=True,font='Courier New',align='left');text('prompt','Prompt : How far the robot is from the origin?',58,383,638,28,22,bold=True,font='Courier New',align='left')
 for id,box in [('mapping-formula',(594,13,725,49)),('language-far-formula',(402,163,530,183)),('language-near-formula',(267,241,374,290)),('distance-formula',(568,250,680,286)),('latent-s-formula',(847,251,900,282)),('latent-sp-formula',(968,161,1027,198)),('gaussian-prior-formula',(938,243,1068,280)),('distance-constraint',(796,376,1095,410))]:image(id,box,'Original isolated mathematical expression; formula pixels remain raster')

 for n in s['nodes']:
  if n.get('dash'):n['dash_style']='dotted';n['dash_pattern']=[1,3]
 s['provenance']['notes']+=' LGSD retains the two original robot illustrations and eight isolated formulas; all ordinary language and the graph geometry are native.'
elif slug=='scaling-up':
 blue='#A2B6FA';stroke='#526AE2';orange='#FF931D'
 for id,x,y,w,h,label in [('clip',440,12,188,111,'CLIP\ntext enc'),('resnet-global',440,139,188,81,'Resnet18'),('resnet-wrist',440,237,188,82,'Resnet18'),('diffusion-policy',457,369,259,111,'Diffusion\nPolicy')]:
  rect(id,x,y,w,h,blue,stroke,6);text(id+'-label',label,x+8,y+7,w-16,h-14,34,stroke,font='Courier New')
 text('task-desc','task desc',5,4,236,37,33,bold=True,font='Courier New',align='left');text('task-instruction','“send the package\nfor return”',20,39,346,70,33,font='Courier New',align='left');text('vision','vision',6,134,185,44,34,bold=True,font='Courier New',align='left')
 image('global-observation',(18,201,184,294),'Original global camera observation, retaining visual content only');image('wrist-observation',(192,170,359,294),'Original wrist camera observation, retaining visual content only')
 # Opaque observation name strips remove old bitmap wording and retain editable labels.
 rect('global-label-strip',18,294,166,44,'#999999','none',0);rect('wrist-label-strip',192,294,167,44,'#555555','none',0);text('global-label','global',18,294,160,44,34,'#FFFFFF',font='Courier New',align='left');text('wrist-label','wrist',194,294,163,44,34,'#FFFFFF',font='Courier New',align='left')
 text('proprioception','proprioception',5,403,300,42,34,bold=True,font='Courier New',align='left');text('gripper-command','gripper pose & command',6,450,445,43,32,font='Courier New',align='left')
 for id,pts in [('task-arrow',[(378,67),(420,67)]),('camera-arrow',[(378,198),(420,198)]),('global-arrow',[(99,339),(99,357),(393,357),(393,284),(421,284)]),('proprio-arrow',[(306,426),(422,426),(422,340),(675,340),(675,356)]),('action-arrow',[(724,446),(850,446)])]:line(id,pts,'#303030',2.5,True,size=10)
 line('feature-concatenation',[(641,67),(676,67),(676,357)],'#333333',2.5,True,size=10);line('global-features',[(643,177),(676,177)],'#333333',2.5);line('wrist-features',[(643,275),(676,275)],'#333333',2.5)
 text('concatenate','concatenate',607,158,220,44,32,font='Courier New',rotation=270)
 image('robot-action-visualization',(775,3,1195,414),'Original robot action illustration, including internal curved orange motion annotations; photo content is raster')
 for i,label in enumerate(['aₜ','aₜ₊₁','aₜ₊₂','aₜ₊₃','aₜ₊₄','···']):rect('action-cell-'+str(i),859+i*52,420,52,52,'#FFF0D9',orange,2);text('action-token-'+str(i),label,860+i*52,428,50,33,28,orange)
 for id,label,x,w in [('inputs','a) Inputs',60,258),('networks','b) Networks',454,292),('action-sequence','c) Action Sequence',805,382)]:text(id,label,x,500,w,39,33,bold=True,font='Courier New')
 s['provenance']['notes']+=' Figure4 is the paper’s policy-distillation architecture. Two observation image assets stop above their name strips; the observation labels exist only as native text and cannot leave hidden original lettering. The robot action illustration includes internal motion annotations as raster; all architecture arrows are native.'
elif slug=='sds':
 gray='#F0F0F0';brown='#A98D69';darkbrown='#936B3C';mid='#939494';ink='#333333'
 rect('outer-cycle',21,17,1148,566,'none','#48526E',1,True,dash=True);rect('learning-panel',517,28,639,538,gray,'#C5C5C5',2,True);rect('prompt-panel',32,115,442,358,brown,'#BBA78C',1,True)
 rect('env-code',45,140,240,155,'none','#FFFFFF',2.5,True);text('env-label','IsaacGym Env Code',65,159,204,30,20,'#FFFFFF',True,font='Times New Roman');text('env-code-live','def get_observation(self):\n  self.root_states = ...\n  self.dof_states = ...\n  self.contact_force = …',87,199,191,76,11,'#FFFFFF',True,font='Courier New',align='left')
 text('gpt-label','GPT-4o',291,143,121,49,34,'#FFFFFF',True,font='Times New Roman');image('gpt-logo',(413,141,471,193),'Original GPT-4o logo icon')
 rect('evolution-prompt',299,217,165,69,'#848485','#E5E5E5',1,True);text('evolution-label','Evolution\nPrompt',304,229,154,50,21,'#FFFFFF',True,font='Times New Roman')
 rect('sus-banner',32,304,442,31,darkbrown,'#E0D7CB',1);text('sus-label','SUS PROMPT',130,304,250,32,31,'#FFFFFF',True,font='Times New Roman')
 image('demonstration-video',(57,346,244,454),'Original layered animal video frames; individual source photo strip');image('contact-sequence-visualization',(267,342,457,448),'Original frame and contact-sequence visual data; internal pixels remain raster')
 rect('generation-dashes',533,45,160,209,'none','#747474',1.8,dash=True);rect('filter-dashes',551,83,127,158,'none',ink,2.7,dash=True);text('generation-heading','RF Generation',537,49,153,30,24,ink,True,font='Times New Roman');text('filter-heading','RF Filtering',555,84,120,28,20,ink,True,font='Times New Roman')
 rect('bad-rf',591,115,58,30,'#DEDEDE',ink,1.5);rect('best-rf',591,177,58,32,'#DEDEDE','#5D5D5D',6);text('bad-rf-label','{RF₁}',594,117,52,27,21,ink,True,font='Times New Roman');text('best-rf-label','{RF₈}',594,179,52,27,21,'#666666',True,font='Times New Roman');text('rf-dots','⋮',601,143,35,31,24,ink,True,font='Times New Roman');line('rf-cross-1',[(568,123),(584,137)],'#D07D81',6);line('rf-cross-2',[(584,122),(568,137)],'#D07D81',6);poly('rf-check',[(562,191),(569,199),(585,185)],'#8D9A7E',6);poly('best-rf-tail',[(622,207),(639,224),(637,207)],'#555555',0,'#555555',True)
 rect('executable-dashes',720,41,414,216,'none','#707070',1.8,dash=True);text('executable-heading','Executable RFs',799,48,257,29,24,ink,True,font='Times New Roman');text('reward-code','def compute_reward(self):\n    env = self.env\n\n    forward_vel_reward = env.base_lin_vel[:,0]\n    angular_vel_penalty = torch.sum(torch.abs(env.base_ang_vel), dim=1)\n\n    ...\n\n    total_reward = forward_vel_reward - angular_vel_penalty + ...\n\n    # return total reward and individual reward components\n    return total_reward, {\n        "forward_vel_reward": forward_vel_reward,\n        "angular_vel_penalty": angular_vel_penalty,',739,82,390,166,8.9,'#333333',font='Courier New',align='left')
 for id,y,title,rows in [('prompt-generation',292,'Evolution Prompt Generation',['Reward Signal Tracking','Best Reward Function']),('reward-evaluation',421,'Reward Function Evaluation',['Contact Sequence','Execution Footage'])]:
  rect(id,549,y,290,115,'#DFD9D5','#C7C4C1',2,True);text(id+'-heading',title,552,y+6,283,27,18,ink,True,font='Times New Roman')
  for j,label in enumerate(rows):rect(id+'-row-'+str(j),575+(10 if y>400 else 0),y+34+j*37,238-(24 if y>400 else 0),31,mid,'none',0,True);text(id+'-label-'+str(j),label,581+(10 if y>400 else 0),y+39+j*37,224-(24 if y>400 else 0),22,16,'#FFFFFF',True,font='Times New Roman')
 image('ppo-training-robots',(886,299,1086,542),'Original simulated quadruped training montage; internal pixels remain raster');text('ppo-label','IsaacGym PPO Training',994,405,249,31,23,ink,True,font='Times New Roman',rotation=90)
 curve('step1',(272,119),(269,78),(285,60),(318,60),'#000000',5);line('step1-final',[(316,60),(514,60)],'#000000',5,True,size=24)
 line('rf-execution',[(688,133),(722,133)],ink,2.5,True,size=9);line('step2',[(982,259),(982,297)],ink,3,True,size=11);line('step3',[(884,341),(814,341)],ink,3.5,True,size=12);line('step4',[(885,478),(835,478)],ink,3.5,True,size=12);line('step5',[(581,489),(381,489)],'#000000',3.5);curve('step5-return',(381,489),(354,489),(355,473),(354,455),'#000000',3.5,True,size=16);line('step6',[(474,378),(575,378)],ink,3.5,True,size=12);line('step7',[(548,329),(507,329),(507,259),(466,259)],'#000000',3.5,True,size=13)
 for num,x,y in [(1,289,82),(2,998,263),(3,852,313),(4,852,448),(5,485,457),(6,485,340),(7,482,220)]:text('step-number-'+str(num),'('+str(num)+')',x,y,36,28,23,bold=True,font='Times New Roman')
 # Two thick source cycle arrow segments are independent native paths.
 path('cycle-top',[{'moveTo':{'x':1053,'y':13}},{'lineTo':{'x':1129,'y':13}},{'cubicBezTo':{'x1':1154,'y1':13,'x2':1174,'y2':33,'x':1174,'y':65}},{'lineTo':{'x':1186,'y':65}},{'lineTo':{'x':1169,'y':82}},{'lineTo':{'x':1152,'y':65}},{'lineTo':{'x':1164,'y':65}},{'cubicBezTo':{'x1':1164,'y1':42,'x2':1153,'y2':22,'x':1128,'y':22}},{'lineTo':{'x':1053,'y':22}},{'close':{}}],'#48526E',1.2,'#999D9E')
 path('cycle-bottom',[{'moveTo':{'x':151,'y':579}},{'lineTo':{'x':57,'y':579}},{'cubicBezTo':{'x1':34,'y1':579,'x2':25,'y2':560,'x':25,'y':542}},{'lineTo':{'x':37,'y':542}},{'lineTo':{'x':22,'y':528}},{'lineTo':{'x':8,'y':542}},{'lineTo':{'x':17,'y':542}},{'cubicBezTo':{'x1':17,'y1':567,'x2':29,'y2':587,'x':56,'y':587}},{'lineTo':{'x':151,'y':587}},{'close':{}}],'#48526E',1.2,'#999D9E');text('cycle-label','SDS x5',50,538,117,38,30,font='Times New Roman')

 for n in s['nodes']:
  if n.get('dash'):n['dash_style']='dotted' if n['id']=='filter-dashes' else 'dashed';n['dash_pattern']=[2,3] if n['id']=='filter-dashes' else [5,4]
 s['provenance']['notes']+=' SDS contains four isolated original visual inserts: logo, demonstration photo frames, contact-sequence visualization and robot simulation montage. Prompt/code, stage numbers and all loop geometry are typeable/native.'
if slug=='sds':
 for n in s['nodes']:
  radius={'outer-cycle':46,'learning-panel':26,'prompt-panel':18,'prompt-generation':20,'reward-evaluation':20,'evolution-prompt':13}.get(n['id'])
  if radius:
   w,h=n['width'],n['height'];r=radius;k=.55228475;n['shape']='path';n['commands']=[{'moveTo':{'x':r,'y':0}},{'lineTo':{'x':w-r,'y':0}},{'cubicBezTo':{'x1':w-r+k*r,'y1':0,'x2':w,'y2':r-k*r,'x':w,'y':r}},{'lineTo':{'x':w,'y':h-r}},{'cubicBezTo':{'x1':w,'y1':h-r+k*r,'x2':w-r+k*r,'y2':h,'x':w-r,'y':h}},{'lineTo':{'x':r,'y':h}},{'cubicBezTo':{'x1':r-k*r,'y1':h,'x2':0,'y2':h-r+k*r,'x':0,'y':h-r}},{'lineTo':{'x':0,'y':r}},{'cubicBezTo':{'x1':0,'y1':r-k*r,'x2':r-k*r,'y2':0,'x':r,'y':0}},{'close':{}}]
validate(s,D);scene=D/(s['id']+'.json');scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True);print(slug,len(s['nodes']))
