INDEX=86;SLUG='robolab';ID='robolab-figure-1';PAGE=1;FIG=1;BBOX=[50, 178, 561, 425]
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
B('framework-title-bar',5,4,1521,36,'#ECECEC','none',0);T('framework-title','RoboLab Benchmarking Framework',492,9,628,31,27,color='#454545',bold=True)
B('analysis-title-bar',5,477,1521,39,'#ECECEC','none',0);T('analysis-title','Policy Performance Analysis',522,482,500,33,29,color='#454545',bold=True)
for k,(x,w,title) in enumerate([(125,409,'Scene Generation'),(548,484,'Task Generation'),(1045,483,'Environment Generation')]):
 B('top-panel-'+str(k),x,52,w,414,'#FFFFFF','#333333',1.5,round=True);T('top-title-'+str(k),title,x+20,61,w-40,34,29);B('top-strip-'+str(k),x+15,100,w-31,78,'#ECECEC','none',0,round=True)
for k,(x,w,title) in enumerate([(6,256,'Multiple Eval Axes'),(280,644,'Metrics'),(939,214,'Sensitivity\nAnalysis'),(1169,358,'Real world correlation')]):
 B('bottom-panel-'+str(k),x,528,w,204,'#FFFFFF','#333333',1.5,round=True);T('bottom-title-'+str(k),title,x+9,533,w-18,54 if k==2 else 34,27,color='#4E4E4E')
# Source example photos are independent insets, not a whole-figure backdrop.
for k,box in enumerate([[148,192,325,324],[333,195,516,324],[148,333,325,449],[334,333,516,449],[560,190,790,304],[794,190,1023,304],[560,324,790,447],[794,324,1023,447],[1060,190,1283,313],[1295,190,1511,313],[1060,324,1283,447],[1295,324,1511,447],[1185,576,1331,720],[148,107,468,173],[632,105,742,174],[1074,104,1510,175],[431,59,499,95],[883,59,950,95]]):IMG('example-'+str(k),box,'Source photographic scene, robot or icon inset; internal pixels remain raster')
B('task-quote-white',657,301,283,34,'#FFFFFF','none',0);T('task-quote','“Put the __ in the blue bin”',657,302,283,29,22)
T('language','Language\ninstruction',799,111,161,51,23);T('task-plus','+',744,112,54,51,48,bold=True)
T('policy-title','Policy',24,63,86,36,29)
for k,(txt,y) in enumerate([('π₁',116),('π₂',176),('⋮',225),('πN',282)]):T('policy-'+str(k),txt,35,y,51,43,35,font='Times New Roman',italic=True)
P('policy-brace',[(89,136),(100,141),(100,210),(110,219),(100,229),(100,297),(90,305)],stroke='#111111',sw=2.3)
B('legend-box',9,374,101,78,'#ECECEC','none',0,round=True);IMG('legend-icons',[18,381,53,443],'Original user and neural-network legend icons only');T('legend-labels','user\nLLM',55,384,51,58,19,color='#4D4D4D',align='left')
for k,t in enumerate(['Competency Categories','Task Difficulty','Language complexity','Task horizon','Scene Complexity']):B('axis-row-'+str(k),27,568+k*31,213,28,'#ECECEC','none',0);T('axis-label-'+str(k),t,29,570+k*31,210,25,19,color='#555555')
# Native illustrative continuous/discrete metric symbols and routes.
C('continuous-green',(305,659),(377,657),(387,607),(438,594),'#58AD39',2.5,head=10);L('continuous-red',[(308,660),(347,657),(387,647),(387,635),(402,635),(396,628),(417,623),(411,618),(443,613)],'#E44930',2.3,head=10)
for k,(x,y,color,txt) in enumerate([(354,615,'#66B45C','✓'),(362,656,'#DE4B43','×'),(484,570,'#D65349','×'),(484,601,'#D65349','×'),(484,631,'#D65349','×'),(484,662,'#66B45C','✓')]):O('metric-ring-'+str(k),x,y,17,17,'#FFFFFF',color,2);T('metric-sign-'+str(k),txt,x,y-1,17,19,17,color=color)
for k,t in enumerate(['Wrong obj grabbed','Gripper collision','Target obj dropped','Target obj grabbed']):T('metric-label-'+str(k),t,508,571+k*30,192,27,21,align='left')
L('metric-divider',[(462,558),(462,715)],'#777777',1,arrow=False);L('performance-divider',[(704,558),(704,715)],'#777777',1,arrow=False)
T('continuous-title','Continuous',306,688,142,30,26);T('discrete-title','Discrete',527,688,122,30,26);T('performance-title','Performance',726,688,181,30,25)
IMG('performance-chart',[714,550,909,685],'Original small performance bar chart, not editable data series; comparison plot only')
L('sensitivity-axis-x',[(990,702),(1124,702)],'#555555',1,arrow=False);L('sensitivity-axis-y',[(993,594),(993,703)],'#555555',1,arrow=False);T('theta','θ',1032,706,24,25,24,font='Times New Roman',italic=True);T('probability','p(θ | succ)',941,635,83,20,19,font='Times New Roman',italic=True)['rotation']=-90
T('benchmark-correlation','Benchmark\nCorrelation',1350,589,162,54,23,italic=True);T('spearman','Spearman ρ=1',1348,650,174,29,23);T('pearson','Pearson r=0.68',1348,680,174,29,23)
for n in s['nodes']:
 if n['id']=='top-title-0':n.update(x=187,width=240,font_size=28)
 if n['id']=='top-title-1':n.update(x=657,width=228,font_size=28)
# Native pi_N uses a real smaller baseline-shifted N, not a full-sized N.
s['nodes']=[n for n in s['nodes'] if n['id']!='policy-3']
T('policy-3-pi','π',35,279,31,43,35,font='Times New Roman',italic=True)
T('policy-3-N','N',59,296,24,29,24,font='Times New Roman',italic=True)
# Measure the source blue silhouette and reproduce its smooth upper envelope as
# editable cubic geometry. This is a visual trace, not invented numerical data.
import numpy as np
from scipy.interpolate import PchipInterpolator
arr=np.asarray(reference.convert('RGB')).astype(float);xx=[];yy=[]
for x in range(995,1121):
 column=arr[595:703,x];mask=(column[:,2]-column[:,0]>15)&(column[:,2]-column[:,1]>5)&(column[:,0]>90)
 ids=np.flatnonzero(mask)
 if len(ids):xx.append(x);yy.append(float(ids[0]+595))
indices=list(range(0,len(xx),3));indices=indices if indices[-1]==len(xx)-1 else indices+[len(xx)-1]
xs=np.array([xx[i] for i in indices]);ys=np.array([yy[i] for i in indices]);inter=PchipInterpolator(xs,ys);der=inter.derivative();x0=float(xs[0]);y0=float(min(ys));commands=[{'moveTo':{'x':0,'y':702-y0}},{'lineTo':{'x':0,'y':float(ys[0]-y0)}}]
for i in range(len(xs)-1):
 a,b=float(xs[i]),float(xs[i+1]);h=b-a
 commands.append({'cubicBezTo':{'x1':a-x0+h/3,'y1':float(ys[i]+der(a)*h/3-y0),'x2':b-x0-h/3,'y2':float(ys[i+1]-der(b)*h/3-y0),'x':b-x0,'y':float(ys[i+1]-y0)}})
commands.extend([{'lineTo':{'x':float(xs[-1]-x0),'y':702-y0}},{'close':{}}])
node('sensitivity-source-curve','path',x0,y0,float(xs[-1]-x0),702-y0,fill='#A3BED9',stroke='#789CC5',stroke_width=1.3,commands=commands)
s['provenance']['notes']+=' Native framework panels, ordinary labels, metric descriptions, continuous curves, sensitivity chart and policy list. Eighteen bounded example photo/icon assets plus legend icons and original small performance plot remain raster; no whole-figure backdrop.'
finish()
