INDEX=87;SLUG='fate';ID='fate-figure-2';PAGE=4;FIG=2;BBOX=[326, 65, 524, 194]
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
# Source conceptual method geometry, editable axes, static plane, and repair documents.
P('static-plane',[(191,150),(342,23),(342,239),(191,367)],'#DFEDF9','none',0,True)
for label,y,color,lines in [('scene',26,'#83B6CD',['{ Remove Asset','Spawn Asset','Set Joint','Rescale','... }']),('policy',202,'#89BE91',['{ Inject Reward','Replan Path','Adjust Grasp','...}'])]:
 B(label+'-back',17,y+12,126,133,'#E4E7E9',color,3)
 P(label+'-document',[(27,y),(120,y),(153,y+29),(153,y+139),(27,y+139)],'#ECEEEF',color,3,True)
 P(label+'-fold',[(120,y),(120,y+29),(153,y+29)],'#D4DBDF','#A0A9AD',1,True)
 for j,t in enumerate(lines):T(label+'-label-'+str(j),t,34,y+20+j*25,108,22,14,align='left')
L('static-repair',[(156,100),(240,100)],'#22677F',2,head=10);L('dynamic-repair',[(79,349),(79,383),(486,383),(486,352)],'#427F34',2,head=10)
L('axis-T',[(352,222),(554,222)],sw=2.2,head=10);L('axis-J',[(357,225),(357,46)],sw=2.2,head=10);L('axis-S',[(356,227),(222,345)],sw=2.2,head=10)
T('axis-t','T',559,206,30,33,28,font='Times New Roman',italic=True);T('axis-j','J',344,7,26,31,28,font='Times New Roman',italic=True);T('axis-s','S',198,335,26,30,28,font='Times New Roman',italic=True)
T('static-title','Static Alignment',230,61,128,22,19,font='Times New Roman',bold=True,italic=True)['rotation']=-44;T('dynamic-title','Dynamic Alignment',396,329,183,28,20,font='Times New Roman',bold=True,italic=True)
B('feasible-label',370,60,188,29,'#C5E7B5','#A7C99A',1);T('feasible-text','Feasible Task-Policy Space',378,65,173,20,12,color='#406442')
# Native low-poly feasible region with translucent-looking flat triangular faces.
verts=[(409,153),(417,122),(433,98),(476,98),(498,126),(505,150),(488,188),(450,187),(428,172)];P('feasible-polytope',verts,'#ACBBAE','none',0,True)
for j,(pts,fill) in enumerate([([(433,98),(462,126),(417,122)],'#BCC8CA'),([(433,98),(476,98),(462,126)],'#9FADBE'),([(476,98),(498,126),(480,148),(462,126)],'#A7B8C1'),([(417,122),(462,126),(444,168),(409,153)],'#BCCABF'),([(462,126),(480,148),(488,188),(444,168)],'#A0B39E'),([(409,153),(444,168),(450,187),(428,172)],'#A7B69D')]):P('face-'+str(j),pts,fill,'none',0,True)
for j,(cx,cy,color) in enumerate([(315,129,'#3CAFE3'),(315,184,'#3CAFE3'),(273,216,'#8DD89F'),(256,276,'#8B8D8C'),(294,253,'#8B8D8C'),(337,290,'#8B8D8C'),(400,303,'#8B8D8C'),(294,337,'#8B8D8C'),(369,191,'#55BB4F'),(431,141,'#55BB4F')]):O('state-'+str(j),cx-5,cy-5,10,10,'#E9EEF0',color,2)
for j,(pts,col) in enumerate([([(315,135),(315,176)],'#94CBE6'),([(311,189),(278,211)],'#94CBE6'),([(273,222),(258,267)],'#BBBBBB'),([(277,220),(291,246)],'#BBBBBB'),([(298,257),(329,284)],'#BBBBBB'),([(343,294),(393,301)],'#BBBBBB'),([(263,281),(289,331)],'#BBBBBB'),([(278,215),(337,209),(365,194)],'#69B55A'),([(374,188),(388,166),(424,151),(429,146)],'#69B55A')]):L('transition-'+str(j),pts,col,1.2,dash=True,head=5)
for id,txt,x,y,w,h,fs,col in [('init','τᵢₙᵢₜ',275,106,48,22,17,'#303030'),('delta','τᵢₙᵢₜ ⊕ Δₛₜₐₜᵢc',208,144,112,24,16,'#303030'),('aper','Aₚₑᵣc (τ)',200,205, 72,25,16,'#303030'),('exec','Aₑₓₑc (τ)',399,105,75,24,16,'#303030'),('eq','θₖ⁽ᵗ⁺¹⁾ ← θₖ⁽ᵗ⁾ ⊕ ∇Lfail(ξfail)',378,232,215,31,14,'#303030'),('fail1','Infeasible',408,296,58,16,10,'#EE2222'),('fail2','Infeasible',305,331,58,16,10,'#EE2222')]:T(id,txt,x,y,w,h,fs,color=col,font='Times New Roman',italic=True)
for j,(txt,x,y) in enumerate([('(a₀,s₀)',202,266),('(a₀,s₀)',287,230),('(a₁,s₁)',325,260),('(a₂,s₂)',380,281),('(a₁,s₁)',275,345)]):T('state-label-'+str(j),txt,x,y,46,19,12,font='Times New Roman',italic=True)
L('alignment-dashed-axis',[(368,200),(368,293)],'#777777',1.2,arrow=False,dash=True)
# Corrections verified against source: document padding, upward repair arrow,
# and explicit native baseline/subscript/superscript mathematical runs.
for n in s['nodes']:
 if n['id']=='scene-label-4':n['y']-=7
s['nodes']=[n for n in s['nodes'] if n['id'] not in ['aper','exec','eq','delta']]
T('delta-tau','τ',207,144,12,22,16,font='Times New Roman',italic=True,align='left')
T('delta-init','init',219,153,19,13,10,font='Times New Roman',italic=True,align='left')
T('delta-oplus','⊕',240,144,18,22,16,font='Times New Roman',italic=True,align='left')
T('delta-base','Δ',258,144,14,22,16,font='Times New Roman',italic=True,align='left')
T('delta-static','static',272,153,28,13,10,font='Times New Roman',italic=True,align='left')
P('alignment-up-arrow',[(368,201),(363.5,211),(372.5,211)],'#000000','none',0,True)
for prefix,x,y,sub in [('aper',201,207,'perc'),('exec',400,107,'exec')]:
 T(prefix+'-base','A',x,y,14,21,17,font='Times New Roman',italic=True,align='left')
 T(prefix+'-subscript',sub,x+11,y+8,24,14,10,font='Times New Roman',italic=True,align='left')
 T(prefix+'-argument','(τ)',x+36,y,29,21,16,font='Times New Roman',italic=True,align='left')
for ident,label,x,y,w,fs in [('eq-theta-next','θ',379,237,12,17),('eq-next-k','k',387,246,9,10),('eq-next-time','(t+1)',389,230,25,10),('eq-left-arrow','←',415,237,20,17),('eq-theta-current','θ',439,237,12,17),('eq-current-k','k',447,246,9,10),('eq-current-time','(t)',449,230,17,10),('eq-oplus','⊕',467,237,18,17),('eq-gradient','∇',486,237,15,17),('eq-loss','L',500,237,11,17),('eq-loss-fail','fail',510,246,18,10),('eq-open','(',528,237,8,17),('eq-xi','ξ',536,237,10,17),('eq-xi-fail','fail',546,246,18,10),('eq-close',')',565,237,8,17)]:
 T(ident,label,x,y,w,20 if fs>10 else 13,fs,font='Times New Roman',italic=True,align='left')
s['provenance']['notes']+=' Fully native conceptual method diagram: axes, alignment plane, feasible polytope, state transitions, action documents and labels. Original soft glows replaced with clean colored outlines; mathematical labels use native typeable runs with explicit baseline, subscript and superscript positions; font metrics approximate the source TeX.'
finish()
