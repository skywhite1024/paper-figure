"""Source-faithful DynScene with repaired encoded text and bounded original renderings."""
import json,sys,subprocess,copy,os
from pathlib import Path
import fitz,numpy as np,contourpy
from PIL import Image
from lxml import etree as ET
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
from paper_figure.model import validate
slug='dynscene';p=json.load(open(R/'data/catalog.json'))['papers'];m=json.load(open(R/'research/survey'/(p[122]['id']+'.json')));pdf=R/m['pdf_path'];c=json.load(open(R/'research/survey/dynscene-config.json'));D=R/'data/diagrams'/slug;s=extract(pdf,c,D);page=fitz.open(pdf)[2];s['nodes']=[n for n in s['nodes']if n['shape']!='text'];original=Image.open(D/(s['id']+'-original.png')).convert('RGB');crop=fitz.Rect(c['crop'])
# Render only the original visual artwork, suppressing all PDF text. This lets
# source photos/room illustrations be cropped without leaving old hidden labels.
doc_no_text=fitz.open(pdf);page_no_text=doc_no_text[2]
for span in page_no_text.get_texttrace():
 r=fitz.Rect(span['bbox'])
 if crop.intersects(r):page_no_text.add_redact_annot(r,fill=None,cross_out=False)
page_no_text.apply_redactions(images=0,graphics=0,text=0)
page_no_text.get_pixmap(matrix=fitz.Matrix(3,3),clip=crop,alpha=False).save(R/'build/dynscene-no-text.png');no_text=Image.open(R/'build/dynscene-no-text.png').convert('RGBA')
# The broad scene panels and all pipeline arrows remain native. Only these
# individual rendered physical objects and their floor surfaces are snapshots.
regions=[('simulator-photo',(1295,251,1458,354)),('static-room-render',(675,374,862,625)),('dynamic-room-render',(1290,372,1474,624)),('residual-pose-10cm',(875,374,998,582)),('residual-pose-20cm',(1000,374,1128,582)),('residual-pose-30cm',(1130,370,1241,582))]
for id,box in regions:
 x,y,x1,y1=box;r=fitz.Rect(box);s['nodes']=[n for n in s['nodes']if not(n['shape']=='path'and r.contains(fitz.Rect(n['x'],n['y'],n['x']+n['width'],n['y']+n['height'])))];name=id+'.png';no_text.crop(box).save(D/name);s['nodes'].append(dict(id=id,shape='image',asset=name,alt='Individual original physical scene/object illustration with its original source text suppressed; internal visual pixels remain raster',x=x,y=y,width=x1-x,height=y1-y))
# Native stepped source-color contours restore the five editable room-layout
# gradient regions. Red pose dots and graph arrows remain independent paths.
def gradient(id,box,mode):
 x,y,x1,y1=box;ar=np.asarray(original.crop(box),dtype=float);r,g,b=ar[:,:,0],ar[:,:,1],ar[:,:,2]
 field=((g>r+3)&(g>b+3))if mode=='green'else((r>g+9)&(g>b+9)&(g>80))if mode=='orange'else((abs(r-g)<4)&(abs(g-b)<4)&(r<240)&(r>125))
 q=(ar.mean(2)//2).astype(int)
 for bucket in sorted(set(q[field].flatten())):
  mask=((q>=bucket)&field).astype(float)
  if not mask.any():continue
  color=np.median(ar[(q==bucket)&field],axis=0).astype(int);fill='#'+''.join(f'{v:02X}'for v in color);pts,offs=contourpy.contour_generator(z=np.pad(mask,1),fill_type='OuterOffset').filled(.5,1.1)
  for k,(pp,oo)in enumerate(zip(pts,offs)):
   pp-=.5;minx=max(0,float(pp[:,0].min()));miny=max(0,float(pp[:,1].min()));maxx=min(x1-x,float(pp[:,0].max()));maxy=min(y1-y,float(pp[:,1].max()));cmd=[]
   if (maxx-minx)*(maxy-miny)<.25:continue
   for st,en in zip(oo[:-1],oo[1:]):
    for j,(a,b)in enumerate(pp[int(st):int(en)]):cmd.append({('moveTo'if j==0 else'lineTo'):{'x':float(a-minx),'y':float(b-miny)}})
    cmd.append({'close':{}})
   s['nodes'].append(dict(id=f'{id}-{bucket}-{k}',shape='path',x=x+minx,y=y+miny,width=max(.01,maxx-minx),height=max(.01,maxy-miny),commands=cmd,fill=fill,stroke='none',stroke_width=0))
for id,box,mode in [('layout-green',(12,353,126,447),'green'),('layout-orange',(203,353,318,447),'orange'),('layout-candidate-green',(61,521,111,571),'green'),('layout-candidate-gray',(119,525,170,573),'gray'),('layout-candidate-orange',(217,525,268,570),'orange')]:gradient(id,box,mode)
def text(id,label,box,fs=20,color='#252323',bold=False,italic=False,font='Arial',rotation=0):
 x,y,x1,y1=box;s['nodes'].append(dict(id=id,shape='text',label=label,x=x,y=y,width=x1-x,height=y1-y,font_size=fs,font_family=font,text_color=color,bold=bold,italic=italic,align='center',text_inset=0,no_wrap=True,rotation=rotation))
for id,label,box,fs,color in [('static-heading','Static Scene Generation',(149,5,480,34),23,'#FF9400'),('action-heading','Action Generation',(797,5,1043,34),23,'#FF9400'),('verification-heading','Verification',(1296,4,1458,34),23,'#FF9400'),('training-heading','Agent Training',(1288,56,1456,86),23,'#BF77A9'),('simulator-heading','Simulator',(1314,216,1447,247),23,'#A1BDE6'),('refinement-heading','Static Scene Refinement',(196,653,490,684),23,'#FF9400'),('augmentation-heading','Action Augmentation',(948,653,1209,684),23,'#FF9400'),('layout-sampling','Layout Sampling',(75,621,263,646),21,'#252323'),('quaternion-heading','Quaternion Quantization',(382,621,639,646),21,'#252323'),('residual-heading','Residual Learning',(975,623,1185,649),21,'#252323'),('static-label','Static Scene',(717,632,834,655),16,'#2454AE'),('dynamic-label','Dynamic Scene',(1307,629,1451,652),16,'#EC2026'),('mismatched','Mismatched\nRoom-Layout',(7,448,126,487),16,'#252323'),('matched','Best matched\nRoom-Layout',(207,448,328,487),16,'#252323'),('room-layouts','Room-Layouts',(101,590,270,615),17,'#252323'),('unstable','Unstable\nOrientation',(370,525,460,566),16,'#252323'),('stable','Stable\nOrientation',(545,525,629,566),16,'#252323'),('goal-state','Goal state',(1294,434,1367,457),15,'#FF0000'),('init-state','Init state',(1367,526,1432,545),14,'#004AAD')]:text(id,label,box,fs,color,True,rotation=325 if id=='init-state'else 0)
for j,x in enumerate([295,896]):text('denoising-label-'+str(j),'Denoising Step x (T-1)',(x,46,x+191,72),18,bold=True,font='Times New Roman')
text('unet-static','U-Net',(354,122,418,145),16,'#4B9B21');text('unet-action','U-Net',(956,122,1020,145),16,'#4B9B21');text('prompt','“Pickup object 10cm”',(268,254,480,281),20,bold=True,italic=True);text('gravity-left','gravity',(401,338,462,365),18);text('gravity-right','gravity',(571,338,633,365),18)
for j,(label,x)in enumerate([('10cm',878),('20cm',1009),('30cm',1138)]):text('residual-length-'+str(j),label,(x,581,x+52,603),16,bold=True)
for id,box in [('state-equation',(96,222,218,274)),('action-equation',(666,220,798,274)),('layout-pose-equation',(95,313,219,349)),('equation6',(133,449,194,473)),('equation7',(480,398,541,427)),('layout-z',(48,486,79,512)),('layout-zhat',(258,484,294,512)),('layout-z1',(69,565,103,590)),('layout-z2',(136,565,175,590)),('layout-zk',(232,565,272,590)),('quaternion-equation',(389,571,462,613)),('stable-quaternion-equation',(562,568,624,613))]:
 x,y,x1,y1=box;name=id+'.png';original.crop(box).save(D/name);s['nodes'].append(dict(id=id,shape='image',asset=name,alt='Original isolated mathematical expression; pixels remain raster',x=x,y=y,width=x1-x,height=y1-y))
s['provenance']['notes']='Original DynScene source layout/colors with native pipeline panels, U-Nets, state grids, arrows, quaternion diagram and separately editable room-layout gradient contours. Corrupt PDF character encoding repaired by accurate source-pixel transcription into live ordinary labels. Six discrete robot/scene visuals are rendered with original source text suppressed, so typed labels leave no hidden originals. Twelve mathematical expressions are isolated raster inserts. Source decorative drop shadows on native arrows omitted. Freeform paths are not attached connectors.';s['provenance']['extraction_warnings_reviewed']=['All corrupt source-font text removed and manually transcribed after pixel inspection. Hundreds of source raster fragments are restricted to six original physical-visual components or native room-layout gradient contours. No full-figure image is embedded. Remaining source transparent arrow/drop-shadow rasters omitted; all logical arrows retain native source geometry.']
validate(s,D);scene=D/(s['id']+'.json');scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
