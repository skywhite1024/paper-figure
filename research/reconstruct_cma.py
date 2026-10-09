"""Faithful native reconstruction of the inspected flattened three-stage CMA diagram."""
import json,math,fitz
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];cid='modality-selection-and-skill-segmentation-via-cross-modality-attention';s=json.loads((ROOT/'research/survey'/f'{cid}.json').read_text());out=ROOT/'data/diagrams/cross-modality-attention';out.mkdir(parents=True,exist_ok=True);N=[]
def box(id,x,y,w,h,fill='#FFFFFF',stroke='#555555',rounded=True,label='',size=12,width=1):N.append(dict(id=id,shape='rounded_rect' if rounded else 'rect',label=label,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=width,font_family='Arial',font_size=size,text_color='#111111',align='center',text_inset=0,no_wrap=True))
def text(id,label,x,y,w,h=20,size=12,rotation=0):N.append(dict(id=id,shape='text',label=label,x=x,y=y,width=w,height=h,font_family='Arial',font_size=size,text_color='#111111',align='center',text_inset=0,no_wrap=True,rotation=rotation))
def path(id,pts,color='#444444',width=.9,fill='none',close=False):N.append(dict(id=id,shape='path',x=0,y=0,width=796,height=252,commands=[{'moveTo':dict(x=pts[0][0],y=pts[0][1])}]+[{'lineTo':dict(x=x,y=y)} for x,y in pts[1:]]+([{'close':{}}] if close else []),stroke=color,stroke_width=width,fill=fill))
def arrow(id,pts,color='#444444'):
 path(id,pts,color);(x1,y1),(x,y)=pts[-2:];a=math.atan2(y-y1,x-x1);L=4;W=1.8
 path(id+'-head',[(x,y),(x-L*math.cos(a)+W*math.sin(a),y-L*math.sin(a)-W*math.cos(a)),(x-L*math.cos(a)-W*math.sin(a),y-L*math.sin(a)+W*math.cos(a))],'none',0,color,True)
def panel(id,x,w,color):
 # Source broad rounded panels retained as native custom paths.
 y=2;h=247;r=42;k=.55228475
 cmd=[{'moveTo':dict(x=x+r,y=y)},{'lineTo':dict(x=x+w-r,y=y)},{'cubicBezTo':dict(x1=x+w-r+k*r,y1=y,x2=x+w,y2=y+r-k*r,x=x+w,y=y+r)},{'lineTo':dict(x=x+w,y=y+h-r)},{'cubicBezTo':dict(x1=x+w,y1=y+h-r+k*r,x2=x+w-r+k*r,y2=y+h,x=x+w-r,y=y+h)},{'lineTo':dict(x=x+r,y=y+h)},{'cubicBezTo':dict(x1=x+r-k*r,y1=y+h,x2=x,y2=y+h-r+k*r,x=x,y=y+h-r)},{'lineTo':dict(x=x,y=y+r)},{'cubicBezTo':dict(x1=x,y1=y+r-k*r,x2=x+r-k*r,y2=y,x=x+r,y=y)},{'close':{}}]
 N.append(dict(id=id,shape='path',x=0,y=0,width=796,height=252,commands=cmd,fill='#FFFFFF',stroke=color,stroke_width=.75))
for id,x,w,color in [('stage1',3,262,'#AFBDE4'),('stage2',267,262,'#E6A7A7'),('stage3',532,261,'#ABCBA7')]:panel(id,x,w,color)
text('stage1-label','Stage One',67,3,125,26,16);text('stage2-label','Stage Two',337,3,125,26,16);text('stage3-label','Stage Three',595,3,137,26,16)
def modalities(prefix,x,y):
 for i,c in enumerate(['#B6D6A7','#B6D6A7','#E89797','#9FC5E6']):box(prefix+'-'+str(i),x+i*28,y,25,27,c,size=10)
 text(prefix+'-camera','Camera',x-1,y+33,54,17,8);text(prefix+'-state','State',x+54,y+33,27,17,8);text(prefix+'-tactile','Tactile',x+82,y+33,28,17,8)
for prefix,x in [('one',11),('two',274)]:
 box(prefix+'-embedding',x,94,108,27,'#FFE79E',label='Embedding',size=11)
 box(prefix+'-cma',x,127,108,31,'#A7C4EF',label='CMA',size=16)
 modalities(prefix+'-inputs',x,167)
box('denoised',171,53,71,26,'#F3CECE',label='Denoised\nActions',size=10)
box('noisy',171,209,71,26,'#F3CECE',label='Noisy\nActions',size=10)
path('denoising-upper',[(171,88),(242,88),(228,135),(183,135)],'#555555',1,'#9EC3E3',True)
path('denoising-lower',[(183,150),(228,150),(242,198),(171,198)],'#555555',1,'#9EC3E3',True)
arrow('conditioning',[(65,94),(65,74),(134,74),(134,144),(167,144)])
text('conditioning-label','Conditioning',121,153,59,21,8)
arrow('denoising-loop',[(242,65),(264,65),(264,222),(243,222)])
arrow('cluster-input',[(328,94),(328,74),(397,74),(397,143),(410,143)])
box('clustering',413,85,25,116,'#CDDFED',label='')
text('clustering-label','Clustering',372,130,107,27,16,90)
box('action-label',469,107,29,34,'#FFE79E');text('action-label-text','Action Label',450,175,66,20,9)
arrow('cluster-out',[(439,124),(468,124)])
# Original staggered primitive-policy stack.
box('policy-back-green',636,27,96,112,'#B3D2AE',stroke='none');box('policy-back-red',625,36,98,107,'#E99E9E',stroke='none');box('policy-front',613,46,100,105,'#A5C0F0',stroke='none',label='Primitive\nAction Policy',size=12)
arrow('action-policy',[(498,123),(611,123)])
box('filter',620,160,99,31,'#CDE1F1',label='Modality Filter',size=10)
arrow('action-filter',[(565,124),(565,175),(619,175)])
modalities('policy-input',616,195)
box('actions',756,96,29,31,'#FFE79E');text('actions-label','Actions',752,133,38,21,10)
arrow('policy-actions',[(733,111),(755,111)])
text('primitive-policy-label','Primitive\nAction Policy',618,79,90,43,12)
# Source policy layers have broad 20px corners, not default small rounded boxes.
for n in list(N):
 if n['id'] in ['policy-back-green','policy-back-red','policy-front']:
  x,y,w,h=n['x'],n['y'],n['width'],n['height'];r=20;k=.55228475
  n['label']='';n['shape']='path';n['commands']=[{'moveTo':dict(x=r,y=0)},{'lineTo':dict(x=w-r,y=0)},{'cubicBezTo':dict(x1=w-r+k*r,y1=0,x2=w,y2=r-k*r,x=w,y=r)},{'lineTo':dict(x=w,y=h-r)},{'cubicBezTo':dict(x1=w,y1=h-r+k*r,x2=w-r+k*r,y2=h,x=w-r,y=h)},{'lineTo':dict(x=r,y=h)},{'cubicBezTo':dict(x1=r-k*r,y1=h,x2=0,y2=h-r+k*r,x=0,y=h-r)},{'lineTo':dict(x=0,y=r)},{'cubicBezTo':dict(x1=0,y1=r-k*r,x2=r-k*r,y2=0,x=r,y=0)},{'close':{}}]
d=dict(schema_version=1,id='cross-modality-attention-figure-2',title=s['title_expected']+' — Figure 2',canvas=dict(width=796,height=252),provenance=dict(paper_title=s['title_expected'],paper_url=s['source_url'],figure='Figure 2',page=3,license=s['license_note'],status='figure_recreation',source_sha256=s['pdf_sha256'],source_crop_pdf_points=[98,71,496,197],notes='Manual reconstruction of all three stages from a flattened original. All labels, modality tiles, denoising/cluster modules, stacked policies and routes are native editable objects; no raster images. Original layout and palette retained, with minor corner-radius, font and line-width approximations. Freeform arrows are not semantically attached connectors.'),nodes=N,edges=[])
(out/'cross-modality-attention-figure-2.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');fitz.open(ROOT/s['pdf_path'])[2].get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(98,71,496,197)).save(out/'cross-modality-attention-figure-2-original.png')
