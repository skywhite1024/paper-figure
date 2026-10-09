INDEX=16
SLUG='safe-skill'
PAGE=3
FIG=2
ID='safe-skill-figure-2'
BBOX=[331.5589904785, 50.0800476074, 539.6400146484, 291.4540100098]
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
green='#AAC889';dark='#4F6F34';gray='#7E7F7E';light='#E0EDCF';blue='#BCD0E9';btext='#315F91'
B('pretrain-panel',13,13,537,316,light,'#5C8139',1.7,round=True,dash=True)
for j,(x,y,w,h) in enumerate([(14,381,515,331),(34,363,515,331),(55,346,494,333)]):B(f'task-panel-{j}',x,y,w,h,'#DCE7F7','#6497DF',1.5,round=True,dash=True)
B('environment1',566,13,48,316,'#F8E5D4','#B82F1A',1.6,round=True);B('environment2',566,346,48,333,'#F8E5D4','#B82F1A',1.6,round=True)
for j,cy in enumerate([171,512]):
 n=T(f'environment-label-{j}','Environment',490,cy-19,200,38,29,color='#B42A15');n['rotation']=90
T('pretrain-label','Safety-Aware Skill Discovery',38,26,466,39,28,color='#435E2B')
B('skill-encoder',72,121,164,80,green,dark,1.8,round=True);B('safety-critic',72,210,164,78,green,dark,1.8,round=True);T('skill-encoder-label','Skill Encoder',82,132,145,28,22,color='#405A2C');T('safety-critic-label','Safety-Critic',84,220,143,29,22,color='#405A2C')
IMG('skill-encoder-equation',[92,164,220,194],'Original skill-encoder mathematical equation');IMG('safety-critic-equation',[77,251,223,282],'Original safety-critic mathematical equation')
B('pretrain-policy',335,124,177,164,green,dark,1.8,round=True);T('pretrain-policy-label','Low-Level Policy',341,132,165,29,22,color='#405A2C');IMG('pretrain-policy-equation',[355,164,497,194],'Original low-level policy mathematical equation')
O('sum',256,188,36,35,light,'#666666',2);T('sum-label','+',257,184,35,39,32,color='#666666')
L('state-input',[(566,85),(424,85),(424,123)],gray,3,head=11);T('state-label-upper','s',411,50,30,37,29,color='#5D5D5D',font='Times New Roman',italic=True)
L('state-encoder',[(424,85),(40,85),(40,161),(72,161)],gray,2,dash=True,head=9);L('state-critic',[(40,161),(40,249),(72,249)],gray,2,dash=True,head=9);L('critic-feedback',[(533,205),(533,308),(40,308),(40,260),(72,260)],gray,2,dash=True,head=9)
L('encoder-sum',[(236,161),(274,161),(274,188)],gray,2,dash=True,head=9);L('critic-sum',[(236,249),(274,249),(274,223)],gray,2,dash=True,head=9);L('sum-policy',[(292,205),(334,205)],gray,2,dash=True,head=9);L('action-upper',[(512,205),(566,205)],gray,3,head=11);T('action-label-upper','a',519,172,31,32,29,color='#5D5D5D',font='Times New Roman',italic=True)
B('high-policy',85,366,184,158,blue,'#5084C2',1.8,round=True);T('high-policy-label','High-Level Policy',90,371,173,31,22,color=btext);IMG('high-policy-equation',[137,402,223,434],'Original high-level policy mathematical equation')
B('low-policy',335,366,177,158,green,dark,1.8,round=True);T('low-policy-label','Low-Level Policy',340,373,168,29,22,color='#405A2C');IMG('low-policy-equation',[355,403,497,434],'Original low-level downstream policy mathematical equation')
B('task-reward',85,582,184,80,blue,'#5084C2',1.8,round=True);T('task-reward-label','Task Reward',108,589,139,31,23,color=btext);IMG('task-reward-equation',[114,623,247,655],'Original task-reward mathematical equation')
P('transfer-arrow',[(415,297),(434,297),(434,332),(445,332),(424,359),(403,332),(415,332)],'#527535','#354F21',1.5,True)
L('high-to-low',[(269,445),(335,445)],gray,3,head=11);T('latent-label','z',289,409,26,30,29,color='#5D5D5D',font='Times New Roman',italic=True);L('action-lower',[(512,445),(566,445)],gray,3,head=11);T('action-label-lower','a',519,410,28,32,29,color='#5D5D5D',font='Times New Roman',italic=True)
L('state-return',[(566,552),(177,552),(177,524)],gray,3,head=11);L('state-low',[(423,552),(423,524)],gray,3,head=11);T('state-label-lower','s',413,550,30,34,29,color='#5D5D5D',font='Times New Roman',italic=True);L('reward-high',[(153,582),(153,524)],gray,2,dash=True,head=9);L('high-reward',[(177,552),(177,582)],gray,2,dash=True,head=9);T('reward-label','r',124,543,27,35,29,color='#5D5D5D',font='Times New Roman',italic=True)
T('downstream-label','Downstream\nTask Learning',335,589,196,72,28,color='#31527D')
# Native neural-network glyphs inside policies, preserving source node counts and links.
for tag,inputs,outputs,color in [('upper',[(406,224),(406,256)],[(440,209),(440,240),(440,271)],'#627F42'),('lower',[(406,460),(406,491)],[(440,446),(440,476),(440,506)],'#627F42'),('high',[(161,444),(161,474),(161,504)],[(193,459),(193,489)],'#5B84BE')]:
 for j,(x,y) in enumerate(inputs):
  L(f'{tag}-in-{j}',[(x-29,y),(x-10,y)],gray,2,head=9)
  for k,(xx,yy) in enumerate(outputs):L(f'{tag}-link-{j}-{k}',[(x,y),(xx,yy)],'#58635A',1.6,arrow=False)
 for k,(x,y) in enumerate(outputs):L(f'{tag}-out-{k}',[(x+9,y),(x+32,y)],gray,2,head=9)
 for k,(x,y) in enumerate(inputs+outputs):O(f'{tag}-neuron-{k}',x-6.5,y-6.5,13,13,color,'#40563A' if tag!='high' else '#305B8E',1.6)
for n in s['nodes']:
 if n.get('dash') and not n['id'].endswith('panel') and not n['id'].startswith('task-panel'):n['dash_style']='dotted'
s['provenance']['notes']+=' All ordinary labels, including two rotated Environment labels, are typeable native text. Six compact formula snippets retain source pixels. Panels, sums, neural icons, feedback routes and transfer arrow are native.'
finish()
