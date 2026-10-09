"""Manual native reconstruction of the inspected Pipette Figure 1."""
import json,sys,hashlib,math,subprocess
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from paper_figure.model import validate
slug='pipette';papers=json.load(open(R/'data/catalog.json'))['papers'];m=json.load(open(R/'research/survey'/(papers[110]['id']+'.json')));pdf=R/m['pdf_path'];page=fitz.open(pdf)[3];D=R/'data/diagrams'/slug;D.mkdir(parents=True,exist_ok=True);crop=[108,62,501,339];page.get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(crop)).save(D/'original.png');im=Image.open(D/'original.png');W,H=im.size
s={'schema_version':1,'id':'pipette-figure-1','title':m['title_expected']+' · Figure 1','canvas':{'width':W,'height':H},'provenance':{'paper_title':m['title_expected'],'paper_url':m['source_url'],'figure':'Figure 1','page':4,'license':m.get('license_note','unverified'),'notes':'Source-layout reconstruction of flattened Pipette framework. All ordinary titles, task proposal, data labels and pipeline stages are live text; panels, data cylinders, cubes and arrows are native. Original laboratory assets, robot scene views, interface screenshots and icons are isolated raster inserts. The screenshot UI and visual photo annotations remain raster. Font metrics and curved arrow coordinates are measured approximations.','status':'figure_recreation','source_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'source_crop_pdf_points':crop,'raster_details':[]},'nodes':[],'edges':[]}
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
 dx=end[0]-prev[0];dy=end[1]-prev[1];l=math.hypot(dx,dy);ux,uy=dx/l,dy/l;b=(end[0]-size*ux,end[1]-size*uy);factor=.9 if color in ['#BBA7FF','#D5A5CC'] else .45;p1=(b[0]-size*factor*uy,b[1]+size*factor*ux);p2=(b[0]+size*factor*uy,b[1]-size*factor*ux);poly(id,[p1,end,p2],color,1.6 if open else 0,'none'if open else color,not open)
def line(id,pts,color='#000000',sw=2,arrow=False,dash=False,head=False,size=10):
 shaft=list(pts)
 if arrow and sw>5:
  ex,ey=pts[-1];px,py=pts[-2];length=math.hypot(ex-px,ey-py);shaft[-1]=(ex-(ex-px)/length*size*.7,ey-(ey-py)/length*size*.7)
 n=poly(id,shaft,color,sw,dash=dash)
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
purple='#8D4DB3';pale='#EBE5F7';arrow='#B291D6';thick='#BBA7FF';font='Times New Roman'
rect('researcher-panel',12,9,230,166,'#FBF9FD','none',0,True);image('researcher-icon',(17,44,89,130),'Original researcher/avatar icon');text('researcher-label','Researcher',14,133,75,21,16,font=font)
for j,label in enumerate(['Task proposal','Goals and constraints','Research ideas','Feedback and revision']):rect('researcher-field-'+str(j),96,20+j*39,141,28,pale,'none',0);text('researcher-field-text-'+str(j),label,95,24+j*39,143,20,16,font=font)
rect('asset-panel',258,9,913,167,'#FFFFFF',purple,1.8,True)
assets=[('experimental-scene',(273,29,440,125),'Experimental\nScene Assets',277,132,165),('experimental-workstations',(457,24,618,127),'Experimental\nWorkstation Assets',455,132,166),('environmental-control',(637,30,807,129),'Environmental Control\nEquipment Assets',635,131,178),('measurement',(832,22,987,128),'Measurement\nInstruments Assets',827,131,162),('tubes-racks',(1000,31,1152,116),'Tubes\nand Racks Assets',1007,131,153)]
for name,box,label,x,y,w in assets:image(name,box,'Original separate laboratory asset group photograph/rendering');text(name+'-label',label,x,y,w,35,15,font=font)
for x in [447,629,815,991]:line('asset-separator-'+str(x),[(x,22),(x,165)],'#7F8096',2,dash=True)
line('researcher-down',[(125,175),(125,191)],thick,11,True,size=14);line('assets-down',[(585,176),(585,191)],thick,11,True,size=14)
rect('platform-panel',11,192,1160,407,'#FFFFFF',purple,1.8,True);image('platform-agent-icon',(25,195,81,243),'Original platform-agent robot icon');text('platform-heading','Pipette Simulation Platform Agent',93,198,570,40,26.5,font=font,align='left')
rect('task-proposal-background',21,253,151,130,pale,'none',0);text('task-proposal','Set up a centrifuge tube o\nperation scenario with a c\nentrifuge, tube rack, centri\nfuge tubes, and pipettes on\nthe experimental table. Th\ne robot grasps a tube from\nthe rack, moves it near the\ncentrifuge, and prepares to\ninsert it into the rotor hole.',26,258,146,117,13,font=font,align='left');text('task-proposal-label','Task proposal',41,383,106,22,16,font=font)
# The original cluster is separated around its existing label so no old lettering remains.
for name,box in [('identified-assets-top',(217,252,318,302)),('identified-assets-left',(193,292,218,330)),('identified-assets-right',(315,289,335,350)),('identified-assets-bottom',(202,333,314,382))]:image(name,box,'Original identified laboratory asset illustration, cropped clear of the native label')
rect('asset-identification-panel',225,302,85,29,pale,'none',0);text('asset-identification','Asset\nIdentification',222,302,94,31,15,font=font)
image('constructed-scene',(357,256,500,370),'Original constructed laboratory scene');text('scene-construction','Scene Construction',345,383,170,23,16,font=font)
for id,pts in [('proposal-to-assets',[(173,323),(193,323)]),('assets-to-scene',[(335,323),(356,323)])]:line(id,pts,arrow,1.5,True,size=8)
def cylinder(id,x,y,w,h,color,label):
 rect(id+'-body',x,y+10,w,h-18,color,'none',0);ellipse(id+'-bottom',x,y+h-20,w,20,color,'none',0)
 for j,cy in enumerate([y+24,y+39]):curve(id+'-ring-'+str(j),(x,cy),(x+w*.25,cy+12),(x+w*.75,cy+12),(x+w,cy),'#FFFFFF',1.8)
 ellipse(id+'-top',x,y,w,23,color,'#FFFFFF',1.8);
 for li,word in enumerate(label.split('\n')):text(id+'-label-'+str(li),word,x+7,y+li*11,w-14,13,11.5,'#FFFFFF',font=font)
cylinder('hdf5',565,233,77,70,'#8E7ACC','HDF5\nData');cylinder('lerobot',565,317,76,68,'#6086C0','Lerobot\nData');image('lerobot-data-thumbnail',(592,347,638,381),'Original robot trajectory sample thumbnail on the data cylinder');line('data-format-conversion',[(603,302),(603,318)],arrow,1.4,True,size=8)
for j,(x,y)in enumerate([(742,258),(713,305),(770,306)]):
 for face,pts in [('top',[(x,y+9),(x+25,y),(x+50,y+9),(x+25,y+21)]),('left',[(x,y+15),(x+21,y+25),(x+21,y+48),(x,y+38)]),('right',[(x+29,y+25),(x+50,y+15),(x+50,y+38),(x+29,y+48)])]:poly(f'vla-cube-{j}-{face}',pts,'none',0,'#A39BCE',True)
text('vla-models','VLA models',709,373,117,21,16,font=font);line('dataset-to-vla',[(643,354),(666,354),(666,297),(699,297)],arrow,1.6,True,size=8);line('vla-to-inference',[(848,297),(873,297)],arrow,1.6,True,size=8)
image('inference-interface',(887,217,1150,371),'Original inference interface screenshots; embedded UI text remains part of the screenshots');text('inference-label','Inference',946,373,120,22,16,font=font)
image('teleoperation-icon',(46,437,128,489),'Original teleoperation operator/computer illustration');text('teleoperation-label','Teleoperation',41,489,110,21,16,font=font);image('camera-view',(42,514,133,581),'Original camera observation scene');text('camera-label','Camera',50,579,88,21,16,font=font)
line('asset-recording-down',[(264,400),(264,433)],thick,16,True,size=23)
for id,label,x,y,w,h in [('action-recording','Action\nRecording',214,452,105,38),('multi-view','Multi-view\nImaging',214,533,105,38),('data-collection','Data\nCollection',394,495,105,38),('data-augmentation','Data\nAugmentation',552,466,38,105),('success','Success\nEvaluation',828,409,116,38)]:
 rect(id+'-panel',x,y,w,h,pale,'none',0,True)
 if id=='data-augmentation':text(id+'-label',label,x-37,y+34,110,40,16,font=font,rotation=270)
 else:text(id+'-label',label,x,y+3,w,h-4,16,font=font)
for id,pts in [('teleop-recording',[(146,471),(214,471)]),('camera-imaging',[(146,552),(214,552)]),('action-data',[(319,471),(447,471),(447,495)]),('image-data',[(319,552),(447,552),(447,533)]),('augmentation-light',[(591,518),(609,518)]),('light-speed',[(738,518),(757,518)]),('speed-camera',[(876,518),(895,518)]),('camera-trajectory',[(1021,518),(1038,518)])]:line(id,pts,arrow,1.5,True,size=8)
line('data-augmentation-arrow',[(506,517),(545,517)],thick,16,True,size=23);line('success-inference',[(886,407),(886,386)],thick,12,True,size=16)
for name,box,label,x,w in [('lighting',(609,466,740,565),'Lighting\nPerturbation',609,130),('speed',(757,465,877,565),'Speed\nPerturbation',755,125),('camera-position',(896,466,1021,566),'Camera Position\nPerturbation',889,138),('trajectory',(1039,465,1147,565),'Trajectory\nPerturbation',1035,117)]:image(name,box,'Original separate robot simulation perturbation visualization');text(name+'-label',label,x,566,w,31,15,font=font)
for id,start,c1,c2,end in [('lighting-success',(689,465),(692,441),(766,428),(828,428)),('speed-success',(812,465),(842,465),(876,453),(886,447)),('camera-success',(954,465),(920,464),(892,452),(886,447)),('trajectory-success',(1093,465),(1090,441),(1002,429),(944,428))]:curve(id,start,c1,c2,end,arrow,1.8,True,size=8)
for gi,(title,xs)in enumerate([('Tube-and-Rack Manipulation Tasks',[10,144]),('Cultureware Handling Tasks',[313,446]),('Process-Instrument Operation Tasks',[617,751]),('Analytical-Instrument Operation Tasks',[914,1047])]):
 x0,x1=xs;text('task-family-'+str(gi),title,x0,604,256,23,15.5,bold=True,font=font)
 for j,(x,y)in enumerate([(x0,633),(x1,632),(x0,733),(x1,731)]):image(f'task-family-{gi}-frame-{j}',(x,y,x+120,min(y+87,821)),'Original individual task-stage laboratory robot frame')
 pink='#D5A5CC';line('task-family-'+str(gi)+'-top-arrow',[(x0+121,683),(x1,683)],pink,10,True,size=13);line('task-family-'+str(gi)+'-down-arrow',[(x1+59,718),(x1+59,735)],pink,10,True,size=13);line('task-family-'+str(gi)+'-bottom-arrow',[(x1,776),(x0+120,776)],pink,10,True,size=13)
validate(s,D);f=D/(s['id']+'.json');f.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
