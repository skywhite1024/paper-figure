"""Reproduce Figure 2 of arXiv:2107.14226v6 from the inspected source PDF.
The right half is one embedded raster in this PDF. Its equation glyphs become
editable contours and its network is restored as measured native paths; the Atari
screen is the sole retained raster inset. No full-panel background is embedded.
"""
import argparse, json, sys
from pathlib import Path
import fitz
import numpy as np
from PIL import Image
import contourpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/disdain');a=p.parse_args()
config=json.loads((ROOT/'research/survey/learning-more-skills-through-optimistic-exploration-config.json').read_text());s=extract(a.pdf,config,a.out)
doc=fitz.open(a.pdf);page=doc[config['page']-1];block=[b for b in page.get_text('dict')['blocks'] if b['type']==1][0]
im=Image.open(__import__('io').BytesIO(block['image'])).convert('RGB'); arr=np.array(im)
# Source pixels 0..137 by 124..253 are the screenshot; all other regions are
# the equation, network boxes, histogram bars, thin arrows and sum operator.
screen=(0,124,137,253);im.crop(screen).save(a.out/'disdain-atari-screen.png')
box=block['bbox'];scale=config['scale'];dx=(box[2]-box[0])/im.width*scale;dy=(box[3]-box[1])/im.height*scale
ox=(box[0]-config['crop'][0])*scale;oy=(box[1]-config['crop'][1])*scale
s['nodes'].append(dict(id='disdain-atari-screen',shape='image',asset='disdain-atari-screen.png',alt='Original Atari game screen; individual raster inset',x=ox+screen[0]*dx,y=oy+screen[1]*dy,width=(screen[2]-screen[0])*dx,height=(screen[3]-screen[1])*dy))
# The equation is source-raster artwork. Trace the observed palette regions
# with interpolated contours, keeping glyph counters and colored H boxes.
colors=np.array([[255,255,255],[0,0,0],[94,94,94],[255,223,113],[179,145,181],[131,187,229],[90,186,167],[153,210,242]],dtype=float)
labels=np.argmin(((arr[:45,:,None,:].astype(float)-colors[None,None,:,:])**2).sum(axis=3),axis=2)
for ci in range(1,len(colors)):
    masks=(labels==ci).astype(float)
    points,offsets=contourpy.contour_generator(z=np.pad(masks,1),fill_type='OuterOffset').filled(.5,1.1)
    for j,(pts,off) in enumerate(zip(points,offsets)):
        pts=pts-.5
        x0=float(pts[:,0].min());y0=float(pts[:,1].min());x1=float(pts[:,0].max());y1=float(pts[:,1].max())
        if (x1-x0)*(y1-y0)<1.5:continue
        commands=[]
        for start,end in zip(off[:-1],off[1:]):
            for k,(x,y) in enumerate(pts[int(start):int(end)]):commands.append({('moveTo' if k==0 else 'lineTo'):{'x':float((x-x0)*dx),'y':float((y-y0)*dy)}})
            commands.append({'close':{}})
        color='#'+''.join(f'{int(v):02X}' for v in colors[ci])
        s['nodes'].append(dict(id=f'disdain-formula-color-{ci}-{j}',shape='path',x=ox+x0*dx,y=oy+y0*dy,width=(x1-x0)*dx,height=(y1-y0)*dy,commands=commands,fill=color,stroke=color,stroke_width=.15*dx,source_detail='Interpolated editable contour of the original raster equation palette'))
# Native smooth panel shapes measured against the original 554x313 bitmap.
# Coordinates below are original raster pixels, uniformly mapped to PDF space.
def path_node(name, commands, fill='none', stroke='#5E5E5E', weight=1.8):
    coords=[]
    for c in commands:
        op,v=next(iter(c.items()))
        for x,y in [('x','y'),('x1','y1'),('x2','y2')]:
            if x in v:coords.append((v[x],v[y]))
    x0=min(x for x,y in coords);y0=min(y for x,y in coords);x1=max(x for x,y in coords);y1=max(y for x,y in coords)
    cc=[]
    for c in commands:
        op,v=next(iter(c.items()));v=dict(v)
        for x,y in [('x','y'),('x1','y1'),('x2','y2')]:
            if x in v:v[x]=(v[x]-x0)*dx;v[y]=(v[y]-y0)*dy
        cc.append({op:v})
    s['nodes'].append(dict(id=name,shape='path',x=ox+x0*dx,y=oy+y0*dy,width=max(.01,(x1-x0)*dx),height=max(.01,(y1-y0)*dy),commands=cc,fill=fill,stroke=stroke,stroke_width=weight*dx,source_detail='Smooth native geometry measured against original raster panel'))
def line(name,pts,weight=1):
    path_node(name,[{('moveTo' if i==0 else 'lineTo'):{'x':x,'y':y}} for i,(x,y) in enumerate(pts)],weight=weight)
def arrow(name,x,y):
    path_node(name,[{'moveTo':{'x':x,'y':y}},{'lineTo':{'x':x-8,'y':y-4}},{'lineTo':{'x':x-8,'y':y+4}},{'close':{}}],fill='#5E5E5E',stroke='none',weight=0)
def rounded(name,x,y,w,h,r,fill,weight=1.8):
    c=[{'moveTo':{'x':x+r,'y':y}},{'lineTo':{'x':x+w-r,'y':y}},{'quadBezTo':{'x1':x+w,'y1':y,'x':x+w,'y':y+r}},{'lineTo':{'x':x+w,'y':y+h-r}},{'quadBezTo':{'x1':x+w,'y1':y+h,'x':x+w-r,'y':y+h}},{'lineTo':{'x':x+r,'y':y+h}},{'quadBezTo':{'x1':x,'y1':y+h,'x':x,'y':y+h-r}},{'lineTo':{'x':x,'y':y+r}},{'quadBezTo':{'x1':x,'y1':y,'x':x+r,'y':y}},{'close':{}}]
    path_node(name,c,fill=fill,weight=weight)
line('disdain-input-branch',[(227,187),(244,187),(244,102),(259,102)])
line('disdain-input-mid',[(244,187),(259,187)])
line('disdain-input-bottom',[(244,187),(244,271),(259,271)])
for k,y in enumerate([102,187,271]):arrow('disdain-input-arrow-'+str(k),260,y)
line('disdain-ensemble-combine',[(361,102),(379,102),(379,271),(361,271)])
line('disdain-ensemble-combine-mid',[(361,187),(396,187)])
arrow('disdain-combine-arrow',396,187)
line('disdain-output-line',[(429,187),(452,187)])
arrow('disdain-output-arrow',452,187)
path_node('disdain-encoder',[{'moveTo':{'x':145,'y':132}},{'lineTo':{'x':224,'y':153}},{'quadBezTo':{'x1':227,'y1':154,'x':227,'y':158}},{'lineTo':{'x':227,'y':219}},{'quadBezTo':{'x1':227,'y1':223,'x':224,'y':224}},{'lineTo':{'x':145,'y':244}},{'quadBezTo':{'x1':142,'y1':245,'x':142,'y':241}},{'lineTo':{'x':142,'y':135}},{'quadBezTo':{'x1':142,'y1':131,'x':145,'y':132}},{'close':{}}],fill='#FFFFFF')
for k,(y,c,widths) in enumerate([(62,'#B391B5',[30,40,20,79,59]),(146,'#83BBE5',[79,49,40,59,20]),(230,'#5ABAA7',[30,40,79,49,30])]):
    rounded('disdain-ensemble-box-'+str(k),263,y,98,82,3,c)
    for j,w in enumerate(widths):rounded(f'disdain-ensemble-bar-{k}-{j}',272,y+10+j*12.5,w,12.5,3,c)
rounded('disdain-output-box',454,146,99,82,3,'#FFDF71')
for j,w in enumerate([59,40,69,79,30]):rounded('disdain-output-bar-'+str(j),464,156+j*12.5,w,12.5,3,'#FFDF71')
# Circle as native cubic outline, preserving the source sum junction.
k=.5522847498307936;r=15.5;cx=413;cy=187
path_node('disdain-sum-circle',[{'moveTo':{'x':cx+r,'y':cy}},{'cubicBezTo':{'x1':cx+r,'y1':cy+k*r,'x2':cx+k*r,'y2':cy+r,'x':cx,'y':cy+r}},{'cubicBezTo':{'x1':cx-k*r,'y1':cy+r,'x2':cx-r,'y2':cy+k*r,'x':cx-r,'y':cy}},{'cubicBezTo':{'x1':cx-r,'y1':cy-k*r,'x2':cx-k*r,'y2':cy-r,'x':cx,'y':cy-r}},{'cubicBezTo':{'x1':cx+k*r,'y1':cy-r,'x2':cx+r,'y2':cy-k*r,'x':cx+r,'y':cy}},{'close':{}}],fill='#FFFFFF')
line('disdain-sum-horizontal',[(cx-r,cy),(cx+r,cy)],1.8)
line('disdain-sum-vertical',[(cx,cy-r),(cx,cy+r)],1.8)
s['provenance']['raster_source_reconstruction']='Right panel original bitmap is not embedded. The Atari screen is isolated; the formula uses editable traced source-pixel paths and the network uses smooth native paths measured from source pixels. Formula antialiasing is approximated by interpolated source-palette contours.'
s['provenance']['extraction_warnings_reviewed']=['The one image warning is resolved by isolated Atari inset and separately traced native network/equation components. Source clipping only bounds the left vector artwork; inspected preview shows no missing geometry.']
# Match the source baseline while retaining ordinary labels as typeable text.
for node in s['nodes']:
    if node['shape']=='text':
        node['y']=max(0,node['y']-.15*node['font_size'])
        if 'Ital' in node.get('source_font',''):node['italic']=True
s['provenance']['text_editability']='Ordinary labels and prose remain native typeable text. Mathematical expressions are editable glyph-outline paths, not live equations.'
s['provenance']['font_substitutions']='Ordinary labels/prose use Arial or Times New Roman, with explicit source-baseline adjustment. Source mathematical fonts and raster formulas use native glyph outlines.'
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(s['id'],len(s['nodes']),'objects')
