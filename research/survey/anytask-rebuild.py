INDEX=91;SLUG='anytask';ID='anytask-figure-2';PAGE=2;FIG=2;BBOX=[70, 62, 551, 196]
import argparse,json,hashlib,math,subprocess,sys,fitz
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description='Faithful manually authored editable recreation of a flattened source figure');p.add_argument('--pdf',required=True);a=p.parse_args()
papers=json.loads((R/'data/catalog.json').read_text())['papers'];paper=papers[INDEX];meta=json.loads((R/'research/survey'/f'{paper["id"]}.json').read_text());D=R/'data/diagrams'/SLUG;D.mkdir(parents=True,exist_ok=True);doc=fitz.open(a.pdf);page=doc[PAGE-1];bbox=fitz.Rect(BBOX);pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=bbox,alpha=False);pix.save(D/(ID+'-original.png'));reference=Image.open(D/(ID+'-original.png'));W,H=reference.size
s={'schema_version':1,'id':ID,'title':paper['title']+' · Figure '+str(FIG),'canvas':{'width':W,'height':H},'provenance':{'paper_title':paper['title'],'paper_url':meta.get('versioned_pdf_url',meta['pdf_url']).replace('/pdf/','/abs/'),'figure':'Figure '+str(FIG),'page':PAGE,'license':meta['license_note'],'status':'figure_recreation','source_sha256':hashlib.sha256(Path(a.pdf).read_bytes()).hexdigest(),'source_crop_pdf_points':BBOX,'notes':'Manually reconstructed after inspecting actual source pixels. Original source is a flattened raster. Layout, native panels, labels and connecting geometry are recreated; no whole-figure raster backdrop. Font metrics and curve/arrow geometry approximated. Small original mathematical/photo details retained only where explicitly noted. Independent target-application QA pending.'},'nodes':[],'edges':[]}
def node(id,shape,x,y,w,h,**kw):
 n={'id':id,'shape':shape,'x':x,'y':y,'width':max(.01,w),'height':max(.01,h),**kw};s['nodes'].append(n);return n
def T(id,txt,x,y,w,h,fs=20,color='#000000',font='Arial',bold=False,italic=False,align='center'):
 return node(id,'text',x,y,w,h,label=txt,font_size=fs,text_color=color,font_family=font,bold=bold,italic=italic,align=align,text_inset=0,no_wrap=True)
def B(id,x,y,w,h,fill='#FFFFFF',stroke='#000000',sw=1.5,round=False,dash=False):
 return node(id,'rounded_rect' if round else 'rect',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,dash=dash)
def O(id,x,y,w,h,fill='#FFFFFF',stroke='#000000',sw=1.5,dash=False):return node(id,'ellipse',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,dash=dash)
def P(id,pts,fill='none',stroke='#000000',sw=1.5,close=False,dash=False):
 xs=[x for x,y in pts];ys=[y for x,y in pts];x0=min(xs);y0=min(ys);commands=[{'moveTo':{'x':pts[0][0]-x0,'y':pts[0][1]-y0}}]+[{'lineTo':{'x':x-x0,'y':y-y0}} for x,y in pts[1:]]
 if close:commands.append({'close':{}})
 return node(id,'path',x0,y0,max(xs)-x0,max(ys)-y0,fill=fill,stroke=stroke,stroke_width=sw,commands=commands,dash=dash)
def L(id,pts,color='#000000',sw=1.5,arrow=True,dash=False,head=8):
 n=P(id,pts,stroke=color,sw=sw,dash=dash)
 if arrow:
  x,y=pts[-1];px,py=pts[-2];theta=math.atan2(y-py,x-px);u=(math.cos(theta),math.sin(theta));v=(-u[1],u[0]);P(id+'-head',[(x,y),(x-head*u[0]+head*.45*v[0],y-head*u[1]+head*.45*v[1]),(x-head*u[0]-head*.45*v[0],y-head*u[1]-head*.45*v[1])],fill=color,stroke='none',sw=0,close=True)
 return n
def C(id,start,c1,c2,end,color='#000000',sw=1.5,arrow=True,dash=False,head=8):
 xs=[q[0] for q in [start,c1,c2,end]];ys=[q[1] for q in [start,c1,c2,end]];x0=min(xs);y0=min(ys);node(id,'path',x0,y0,max(xs)-x0,max(ys)-y0,fill='none',stroke=color,stroke_width=sw,dash=dash,commands=[{'moveTo':{'x':start[0]-x0,'y':start[1]-y0}},{'cubicBezTo':{'x1':c1[0]-x0,'y1':c1[1]-y0,'x2':c2[0]-x0,'y2':c2[1]-y0,'x':end[0]-x0,'y':end[1]-y0}}])
 if arrow:
  x,y=end;theta=math.atan2(y-c2[1],x-c2[0]);u=(math.cos(theta),math.sin(theta));v=(-u[1],u[0]);P(id+'-head',[(x,y),(x-head*u[0]+head*.45*v[0],y-head*u[1]+head*.45*v[1]),(x-head*u[0]-head*.45*v[0],y-head*u[1]-head*.45*v[1])],fill=color,stroke='none',sw=0,close=True)
def IMG(id,box,alt):
 x0,y0,x1,y1=box;pb=fitz.Rect(bbox.x0+x0/3,bbox.y0+y0/3,bbox.x0+x1/3,bbox.y0+y1/3);page.get_pixmap(matrix=fitz.Matrix(6,6),clip=pb,alpha=False).save(D/(id+'.png'));node(id,'image',x0,y0,x1-x0,y1-y0,asset=id+'.png',alt=alt)
def finish():
 f=D/(ID+'.json');f.write_text(json.dumps(s,ensure_ascii=False,indent=2));cfg={'id':ID,'paper_title':paper['title'],'paper_url':s['provenance']['paper_url'],'figure':s['provenance']['figure'],'page':PAGE,'crop':BBOX,'scale':3,'license':meta['license_note'],'notes':s['provenance']['notes']};(R/'research/survey'/f'{SLUG}-config.json').write_text(json.dumps(cfg,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/SLUG),'--preview','--force'],cwd=R,check=True)
# Three stacked code/simulation/data cards, original stage labels and routes.
for k,(x,w,fill) in enumerate([(436,200,'#F0CDEF'),(659,200,'#C9EEF9'),(880,201,'#F7F0C7')]):
 for depth in [2,1,0]:B(f'card-{k}-{depth}',x+depth*7,25-depth*9,w,368,fill,'#333333',1.6,round=True)
 B(f'card-badge-{k}',x+30,29,w-43,49,['#DDA2DE','#88D4F0','#F5CF52'][k],'none',0,round=True)
for id,box in [('python-icon',[477,24,531,79]),('simulation-icon',[681,33,728,76]),('data-icon',[898,37,946,68]),('raw-assets-icon',[41,20,104,81]),('database-icon',[302,39,333,85]),('objects-photo',[53,270,151,310]),('simulation-photos',[671,96,848,219]),('collection-photos',[898,93,1066,155]),('real-policy-photos',[1108,100,1435,320]),('robot-arm-icon',[1169,38,1220,86])]:IMG(id,box,'Original discrete source icon/photo inset; its internal pixels remain raster')
B('vlm-panel',145,38,106,43,'#FCE4D5','none',0,round=True);B('task-generator',233,153,172,44,'#DCF2CE','none',0,round=True);B('simulation-generator',233,331,171,57,'#F0CDEE','none',0,round=True);B('policy-panel',1160,27,174,58,'#F2AE86','none',0,round=True)
IMG('policy-arm-icon-visible',[1169,38,1210,81],'Original small robot arm pictogram only')
font='Courier New'
for id,txt,x,y,w,h,fs in [('code-title','Code',542,39,68,26,20),('simulation-title','Simulation',732,42,122,26,20),('data-title','Data\nCollection',946,30,122,49,20),('raw-title','Raw Assets',26,78,125,24,18),('vlm','VLM+LLM',155,49,88,24,18),('database','Object Database',237,88,167,24,18),('taskgen','Task Generator',242,163,160,24,18),('objectlist','Object List',43,241,126,24,18),('taskdescription','Task Description',226,241,183,24,18),('simgen','Simulation\nGenerator',251,339,132,46,18),('policy','(Sim2Real)\nPolicy',1210,32,117,47,19),('code1','Scene Generation/\nreset()',445,110,183,47,18),('code2','check_success()',453,188,176,24,18),('code3','scripted_policy()',443,241,188,25,18),('code4','reward_function()',446,295,184,25,18),('code5','compose_state()',453,349,172,25,18),('simlist','• Parallelized Sim\n• Domain\n  Randomization',663,234,193,70,18),('simdetails','Lighting\nTexture\nMaterial\nObject pose\nJoint state',699,301,121,80,13),('datalist','• Agents\n  ViPR\n  ViPR Eureka\n  ViPR RL\n\n• Data\n  RGB\n  Point Cloud\n  Dense language\n    annotation',895,186,177,183,16)]:T(id,txt,x,y,w,h,fs,font=font,align='left' if id in ['simlist','simdetails','datalist']else'center')
for id,txt,x,y,w,h,fs in [('high-task','High-level Task',18,124,173,25,18),('scenario','Scenario',67,167,100,24,18),('apis','Simulation APIs',27,339,167,24,18)]:T(id,txt,x,y,w,h,fs,color='#EE0909',font=font)
T('api-detail','Environment APIs\nRobot Skill APIs',54,361,142,30,13,color='#B6481F',font=font);T('high-example','“put the item into the drawer”',15,146,194,19,12,color='#909090',italic=True);T('scene-example','Table-top, Franka robot, workspace',4,187,219,18,12,color='#909090',italic=True);T('task-example','“open the drawer, pick up the strawberry,\nand put it into the drawer”',194,263,239,34,12,color='#909090',italic=True)
for k,pts in enumerate([[(115,58),(137,58)],[(267,58),(290,58)],[(318,120),(318,142)],[(198,172),(218,172)],[(231,218),(204,231)],[(317,218),(317,235)],[(169,310),(215,324)],[(316,302),(316,322)],[(201,362),(219,352)],[(410,360),(430,360)],[(638,216),(658,216)],[(865,216),(888,216)],[(1092,216),(1108,216)]]):L('route-'+str(k),pts,sw=1.5,head=8)
s['provenance']['notes']+=' Manually reconstructed stacked stage panels, stage routes, labels and monospaced code names. Only ten bounded photographic/icon assets remain raster; code and ordinary labels typeable.'
finish()
