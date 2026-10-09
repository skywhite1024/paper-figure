INDEX=25
SLUG='deep-skill-graphs'
PAGE=4
FIG=2
ID='deep-skill-graphs-figure-2'
BBOX=[52.3911209106, 65.5555725098, 544.8330078125, 205.1731567383]
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
blue='#4CBFF4';edge='#125C7E';pale='#BEE8FA';pink='#C6A8BA';green='#C7E5A5'
for j,x in enumerate([20,540,1060]):B(f'panel-{j}',x,76,399,294,blue,edge,5,round=True)
L('separator1',[(477,16),(477,412)],sw=2.5,arrow=False);L('separator2',[(1000,16),(1000,412)],sw=2.5,arrow=False)
for j,dx in enumerate([0,520,1040]):
 # Original five-node graph and its two selected path segments.
 C(f'edge-a-{j}',(76+dx,218),(82+dx,201),(90+dx,191),(111+dx,181),'#D42A15' if j==1 else '#000000',6 if j==1 else 2.6,head=12)
 C(f'edge-b-{j}',(169+dx,169),(198+dx,166),(218+dx,175),(235+dx,189),'#D42A15' if j==1 else '#000000',6 if j==1 else 2.6,head=12)
 C(f'edge-c-{j}',(141+dx,203),(141+dx,226),(150+dx,245),(166+dx,255),sw=2.6,head=11)
 C(f'edge-d-{j}',(97+dx,267),(119+dx,283),(143+dx,287),(164+dx,280),sw=2.6,head=11)
 C(f'edge-e-{j}',(220+dx,264),(232+dx,255),(239+dx,248),(246+dx,240),sw=2.6,head=11)
 for k,(cx,cy) in enumerate([(75,246),(142,175),(192,270),(256,214)]):O(f'node-{j}-{k}',cx+dx-28,cy-28,56,56,green if k==3 and j>0 else pale,'#4C727E',3.2)
 O(f'goal-{j}',327+dx,102,56,56,pink,'#50606D',3.2)
T('caption1','Identify goal region',55,324,330,38,31,bold=True);T('caption2','Plan inside the graph',565,324,350,38,31,bold=True);T('caption3','Extend the graph',1090,324,350,38,31,bold=True)
C('goal-expansion',(1367,125),(1328,112),(1302,133),(1297,181),sw=2.6,dash=True,head=10);C('new-node-path',(1318,235),(1336,248),(1353,241),(1360,224),sw=2.6,dash=True,head=10);C('new-goal-path',(1398,183),(1413,178),(1413,163),(1415,155),sw=2.6,dash=True,head=10);O('new-node',1344,171,57,57,pale,'#456779',3.2,dash=True)
for n in s['nodes']:
 if n.get('dash'):n['dash_style']='dotted'
s['provenance']['notes']+=' Fully native recreation: three editable panel labels, graph nodes, curves, selected red path, expansion links and dot markers. No raster content.'
finish()
