INDEX=28
SLUG='rvic'
PAGE=2
FIG=1
ID='rvic-figure-1'
BBOX=[319.5, 54.003219604, 551.341064453, 274.534973145]
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
orange='#FFDDB1';blue='#A3C1F8';purple='#F2C5F2';green='#D1EB66'
B('interaction-panel',143,2,411,354,orange,sw=1.8);B('environment',165,27,368,82,green,sw=1.8);T('environment-label','Environment',195,45,307,48,29)
B('state',165,138,168,85,blue,sw=1.8);T('state-label','State',174,149,150,31,29);IMG('state-formula',[235,184,270,222],'Original state subscript formula')
B('action',365,138,168,85,blue,sw=1.8);T('action-label','Action',373,149,152,31,29);IMG('action-formula',[434,184,470,222],'Original action subscript formula')
B('policy',165,249,368,85,purple,sw=1.8,dash=True);T('policy-label','Skill-Conditioned Policy',181,256,337,40,29);IMG('policy-formula',[263,296,431,331],'Original skill-conditioned mathematical policy formula')
B('skill',4,383,150,86,blue,sw=1.8);T('skill-label','Skill',24,393,110,34,28);IMG('skill-formula',[23,433,135,464],'Original skill sampling equation')
B('reward',163,383,372,86,blue,sw=1.8);T('reward-label','Reward',253,392,192,34,29);IMG('reward-formula',[175,430,526,467],'Original reward difference equation; small formula strip remains raster')
B('trajectory',544,383,150,86,blue,sw=1.8);T('trajectory-label','Trajectory',548,393,142,34,29);IMG('trajectory-formula',[562,430,680,466],'Original trajectory subscript formula')
B('discriminator-panel',143,493,411,167,orange,sw=1.8);T('discriminator-label','Skill Discriminators',170,503,355,38,29);B('relative-discriminator',154,551,190,84,purple,sw=1.8,dash=True);B('absolute-discriminator',354,551,190,84,purple,sw=1.8,dash=True)
IMG('relative-discriminator-formula',[163,580,335,620],'Original relative skill discriminator equation');IMG('absolute-discriminator-formula',[368,580,535,620],'Original absolute skill discriminator equation')
L('environment-state',[(249,109),(249,138)],sw=1.6,arrow=False);L('state-policy',[(249,223),(249,249)],sw=1.6,head=12);L('policy-action',[(449,249),(449,223)],sw=1.6,arrow=False);L('action-environment',[(449,138),(449,110)],sw=1.6,head=12);L('policy-trajectory',[(533,292),(620,292),(620,383)],sw=1.6,arrow=False);L('trajectory-discriminators',[(620,469),(620,576),(554,576)],sw=1.6,head=12);L('skill-policy',[(79,383),(79,292),(165,292)],sw=1.6,head=12);L('skill-discriminators',[(79,469),(79,576),(143,576)],sw=1.6,head=12);L('reward-policy',[(349,383),(349,334)],sw=1.6,head=12)
s['provenance']['notes']+=' Ordinary labels are live typeable text. Nine small equation strips preserve source mathematical typography; architecture panels and routing arrows are native objects.'
finish()
