INDEX=33
SLUG='dads'
PAGE=3
FIG=2
ID='dads-figure-2'
BBOX=[126.5559997559, 149.4858093262, 304.7524414063, 299.0390014648]
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
 x0,y0,x1,y1=box;pb=fitz.Rect(bbox.x0+x0/3,bbox.y0+y0/3,bbox.x0+x1/3,bbox.y0+y1/3);page.get_pixmap(matrix=fitz.Matrix(6,6),clip=pb,alpha=False).save(D/(id+'.png'));im=Image.open(D/(id+'.png')).convert('RGBA'); im.putdata([(0,0,0,max(0,min(255,int((100-min(rr,gg,bb))*255/70)))) for rr,gg,bb,aa in im.getdata()]); im.save(D/(id+'.png'));node(id,'image',x0,y0,x1-x0,y1-y0,asset=id+'.png',alt=alt)
def finish():
 f=D/(ID+'.json');f.write_text(json.dumps(s,ensure_ascii=False,indent=2));cfg={'id':ID,'paper_title':paper['title'],'paper_url':s['provenance']['paper_url'],'figure':s['provenance']['figure'],'page':PAGE,'crop':BBOX,'scale':3,'license':meta['license_note'],'notes':s['provenance']['notes']};(R/'research/survey'/f'{SLUG}-config.json').write_text(json.dumps(cfg,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/SLUG),'--preview','--force'],cwd=R,check=True)
B('intrinsic-panel',143,86,337,214,'#F0F0F0','#000000',2.2,dash=True);s['nodes'][-1]['dash_style']='dash-dot'
B('skill',4,49,115,45,'#C7DEB9','#6D7566',1.4);T('skill-label','skill',29,50,66,24,21,font='Times New Roman');IMG('skill-formula',[27,73,100,94],'Original latent-skill sampling formula')
T('sample-skill-label','sample one skill per\nepisode from the\nprior distribution',1,0,117,44,13,font='Times New Roman');T('intrinsic-label','Intrinsic Reward\nComputation',156,90,101,31,13,bold=True,font='Times New Roman')
P('skill-dynamics',[(269,111),(423,94),(423,183),(269,165)],'#ADC3EB','#707887',1.4,True);T('dynamics-label','skill-dynamics',278,116,133,28,21,font='Times New Roman');IMG('dynamics-equation',[301,140,398,163],'Original skill-dynamics conditional density formula')
T('train-dynamics','train the\nskill-dynamics to\nmaximize the\ntransition probability\nof (s, z) -> s′',288,0,133,70,13,font='Times New Roman')
B('reward-ratio',161,208,144,81,'#D5E4C7','#7E8777',1.4);IMG('reward-ratio-equation',[168,220,298,279],'Original intrinsic reward ratio equation; exact source formula retained')
T('sample-set','sample a set of',319,263,102,18,13,font='Times New Roman');T('sample-set-formula','z′ ~ p(z)',329,279,82,17,13,font='Times New Roman',italic=True)
P('agent',[(89,347),(204,320),(204,428),(89,401)],'#A7C2EF','#727C8A',1.4,True);T('agent-label','agent',107,352,84,27,23,font='Times New Roman');IMG('agent-policy',[109,378,192,402],'Original agent policy equation')
B('environment',260,342,173,63,'#BFD7AA','#718066',1.4);T('environment-label','environment',270,348,153,28,23,font='Times New Roman');IMG('environment-equation',[296,377,420,401],'Original environment dynamics equation')
B('reward-square',46,327,31,29,'#000000','#333333',1)
L('skill-down',[(62,94),(62,326)],'#555555',1.3,arrow=False);L('square-agent',[(62,356),(62,374),(89,374)],'#555555',1.3,head=8);L('agent-action',[(204,374),(260,374)],'#555555',1.3,head=8)
L('outer-loop',[(119,71),(512,71),(512,374),(433,374)],'#666666',1.3,arrow=False);L('state-model-input',[(512,192),(479,192)],'#666666',1.3,head=8);L('state-current',[(433,374),(467,374),(467,309),(62,309)],'#666666',1.3,arrow=False);L('ratio-output',[(143,193),(62,193)],'#666666',1.3,arrow=False);L('density-to-ratio',[(269,138),(233,138),(233,208)],'#777777',1.3,head=8);L('skill-samples-density',[(305,249),(455,249),(455,138),(423,138)],'#777777',1.3,head=8)
for id,txt,x,y,w,h in [('z-top','z',210,52,18,22),('z-left','z',38,130,18,22),('action-label','a',216,372,18,22),('next-state','s′',509,272,26,28),('state-prime','s′',277,309,25,25)]:T(id,txt,x,y,w,h,17,font='Times New Roman',bold=True)
IMG('intrinsic-reward-label',[76,170,136,190],'Original reward mathematical annotation');T('samples-label','z, {z′}',353,228,65,22,17,font='Times New Roman',bold=True)
T('train-agent','train the agent\nto maximize the\nreward r(s′, s, z)',218,408,113,40,12,font='Times New Roman')
s['provenance']['notes']+=' Ordinary annotations are live text. Six compact source mathematical formula snippets retained; policy/model/environment blocks, signal routing and reward computation structure native. Flat fills approximate original gradients.'
finish()
