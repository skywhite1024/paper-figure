INDEX=35
SLUG='valor'
PAGE=4
FIG=1
ID='valor-figure-1'
BBOX=[345.6019897461, 376.6875, 503.9981689453, 500.8469848633]
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
 x0,y0,x1,y1=box;x1=min(x1,W);y1=min(y1,H);pb=fitz.Rect(bbox.x0+x0/3,bbox.y0+y0/3,bbox.x0+x1/3,bbox.y0+y1/3);page.get_pixmap(matrix=fitz.Matrix(6,6),clip=pb,alpha=False).save(D/(id+'.png'));node(id,'image',x0,y0,x1-x0,y1-y0,asset=id+'.png',alt=alt)
def finish():
 f=D/(ID+'.json');f.write_text(json.dumps(s,ensure_ascii=False,indent=2));cfg={'id':ID,'paper_title':paper['title'],'paper_url':s['provenance']['paper_url'],'figure':s['provenance']['figure'],'page':PAGE,'crop':BBOX,'scale':3,'license':meta['license_note'],'notes':s['provenance']['notes']};(R/'research/survey'/f'{SLUG}-config.json').write_text(json.dumps(cfg,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/SLUG),'--preview','--force'],cwd=R,check=True)
B('average-pooling',53,64,370,38,'#FFF3CD','#E3C875',1.3,round=True);T('pooling-label','Average Pooling',134,68,210,30,18);T('logits-label','logits',210,7,57,24,18);L('output',[(238,64),(238,35)],'#777777',1.8,head=8)
xs=[41,120,279,355]
for j,x in enumerate(xs):
 B(f'linear-{j}',x+14,126,58,25,'#D8EACD','#87B873',1.4,round=True);T(f'linear-label-{j}','Linear',x+16,127,54,22,16)
 B(f'top-cell-{j}',x,175,50,47,'#D8E6FC','#87A9D9',1.5,round=True);B(f'bottom-cell-{j}',x,251,50,48,'#D8E6FC','#87A9D9',1.5,round=True)
 L(f'linear-to-pool-{j}',[(x+43,126),(x+43,102)],'#777777',1.6,head=8);L(f'top-to-linear-{j}',[(x+25,175),(x+25,152)],'#777777',1.6,head=8);L(f'input-bottom-{j}',[(x+25,347),(x+25,299)],'#777777',1.6,head=8)
 C(f'input-top-{j}',(x+24,313),(x-35,325),(x-29,231),(x+24,225),'#777777',1.6,head=8)
 C(f'bottom-linear-{j}',(x+49,252),(x+85,253),(x+62,173),(x+62,152),'#777777',1.6,head=8)
for j,(a,b) in enumerate([(120,91),(279,245),(355,330)]):L(f'backward-horizontal-{j}',[(a,198),(b,198)],sw=1.8,head=9)
for j,(a,b) in enumerate([(91,120),(170,193),(245,279),(329,355)]):L(f'forward-horizontal-{j}',[(a,275),(b,275)],sw=1.8,head=9)
T('top-ellipsis','...',206,188,26,23,23,font='Times New Roman',bold=True);T('bottom-ellipsis','...',206,265,26,23,23,font='Times New Roman',bold=True)
for j,b in enumerate([[44,352,93,374],[120,352,177,374],[277,352,337,374],[353,352,414,374]]):IMG(f'state-difference-{j}',b,'Original small mathematical state-difference label only; not live equation')
s['provenance']['notes']+=' Ordinary labels are typeable. Four tiny original state-difference formula labels remain raster; all LSTM cells, bidirectional routes, linear projections and pooling are native.'
finish()
