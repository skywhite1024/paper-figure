"""Native source-layout reconstruction of RoboSubtaskNet Figure2 panels."""
import json,math,fitz
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];cid='robosubtasknet-temporal-sub-task-segmentation-for-human-to-robot-skill-transfer-in-real-world-environments';s=json.loads((ROOT/'research/survey'/f'{cid}.json').read_text());out=ROOT/'data/diagrams/robosubtasknet';out.mkdir(parents=True,exist_ok=True);fitz.open(ROOT/s['pdf_path'])[2].get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(53,49,560,190)).save(out/'robosubtasknet-figure-2-original.png');im=Image.open(out/'robosubtasknet-figure-2-original.png');N=[]
def box(id,x,y,w,h,fill='#FFFFFF',stroke='#888888',width=.7,rounded=False,label='',size=13,bold=False):N.append(dict(id=id,shape='rounded_rect' if rounded else 'rect',x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=width,label=label,font_family='Times New Roman',font_size=size,bold=bold,text_color='#111111',align='center',text_inset=0,no_wrap=True))
def text(id,label,x,y,w,h=23,size=14,bold=False):N.append(dict(id=id,shape='text',label=label,x=x,y=y,width=w,height=h,font_family='Times New Roman',font_size=size,bold=bold,text_color='#111111',align='center',text_inset=0,no_wrap=True))
def poly(id,pts,color='#555555',width=.6,fill='none',close=False):N.append(dict(id=id,shape='path',x=0,y=0,width=1014,height=282,commands=[{'moveTo':dict(x=pts[0][0],y=pts[0][1])}]+[{'lineTo':dict(x=x,y=y)} for x,y in pts[1:]]+([{'close':{}}] if close else []),stroke=color,stroke_width=width,fill=fill))
def arrow(id,pts):
 poly(id,pts);(a,b),(x,y)=pts[-2:];r=math.atan2(y-b,x-a);L=4;W=1.6;poly(id+'-head',[(x,y),(x-L*math.cos(r)+W*math.sin(r),y-L*math.sin(r)-W*math.cos(r)),(x-L*math.cos(r)-W*math.sin(r),y-L*math.sin(r)+W*math.cos(r))],'none',0,'#333333',True)
box('panel-a',2,3,454,249,'#D8E7FA','#84A1BF',.8);box('panel-b',483,6,526,246,'#F5F5F5','#999999',.7)
box('input-block',492,24,223,105,'#DAE7FA','#A9C3E2',.6);box('fusion-block',492,134,223,114,'#DAE7FA','#A9C3E2',.6);box('attention-block',742,20,259,228,'#DAE7FA','#A9C3E2',.6)
for i,r in enumerate([(8,42,95,123),(125,42,215,123),(75,134,179,231)]):
 name=f'frames-{i}.png';im.crop(r).save(out/name);N.append(dict(id='frames'+str(i),shape='image',asset=name,alt='Original demonstration/RGB/optical-flow frame stack; pixels within frames remain raster',x=r[0],y=r[1],width=r[2]-r[0],height=r[3]-r[1]))
text('human','Human\nDemonstration',14,4,83,34,14,True);text('rgb-data','RGB\nVideo Data',134,4,70,34,14,True);text('optical-data','Optical Flow Data',63,230,130,23,14,True)
arrow('human-rgb',[(97,81),(123,81)]);arrow('human-flow',[(48,124),(48,167)]);box('farneback',18,168,45,40,'#FFF3CA',label='Farneback\nOptical\nFlow',size=10);arrow('farneback-flow',[(63,188),(74,188)])
box('spatial',236,35,91,105,'#D9E7F6','#697B8F',.8,True);text('spatial-title','Spatial Stream\nSubnetwork',237,36,89,32,12)
box('temporal',193,135,100,97,'#D9E7F6','#697B8F',.8,True);text('temporal-title','Temporal Stream\nSubnetwork',195,136,96,31,12)
def prism(id,x,y,w,h):
 poly(id+'top',[(x,y),(x+w,y),(x+w+14,y+13),(x+14,y+13)],'#B46D6D',.6,'#EDC7C7',True);poly(id+'side',[(x,y),(x+14,y+13),(x+14,y+h+13),(x,y+h)],'#B46D6D',.6,'#E4B9B9',True);box(id+'front',x+14,y+13,w,h,'#F0CBCB','#B46D6D',.6,label='Inflated 3-D\nConvolution\nNetwork',size=10)
prism('spatial-cnn',239,67,69,52);prism('temporal-cnn',200,167,68,50)
arrow('rgb-spatial',[(217,81),(235,81)]);arrow('flow-temporal',[(179,188),(192,188)])
box('fusion',305,164,84,44,'#FFF3CA','#777777',.8,True,label='Attention Fusion\nBlock',size=12)
arrow('spatial-fusion',[(327,81),(350,81),(350,163)]);arrow('temporal-fusion',[(294,184),(304,184)])
box('fused-feature',370,62,79,39,'#8CD9E8','#777777',.7,True,label='Fused Feature',size=12);arrow('fusion-feature',[(390,186),(410,186),(410,102)])
text('input-title','Input Block',535,6,134,22,16,True);text('fusion-title','Fusion',511,136,56,25,16,True);text('attention-title','Attention\nCalculation',816,209,137,37,16,True)
for id,label,x,y,w,h,size in [('received-rgb','Received\nRGB features',498,33,86,40,14),('transpose-rgb','Transpose RGB\nfeatures',597,33,105,40,14),('received-flow','Received\nFlow features',498,81,86,44,14),('transpose-flow','Transpose Flow\nfeatures',597,81,105,44,14),('linear-rgb','Linear\nTransform\nRGB\nfeatures',752,32,78,79,14),('linear-flow','Linear\nTransform\nFlow\nfeatures',914,32,82,79,14),('sigmoid','Sigmoid',840,91,67,20,14),('compute','Compute attention weights alpha\n(α)',769,128,214,43,14),('mul-flow','Multiply (1-αflow) with\nFlow features',579,138,126,53,14),('mul-rgb','Multiply αrgb with\nRGB Features',576,196,130,43,14),('fused','Fused\nfeatures',496,174,52,35,14)]:box(id,x,y,w,h,label=label,size=size)
for id,x,y in [('sigma-attn',873,55),('sigma-fusion',566,188)]:
 N.append(dict(id=id,shape='ellipse',x=x-10,y=y-10,width=20,height=20,fill='#FFFFFF',stroke='#777777',stroke_width=.7,label='Σ',font_family='Times New Roman',font_size=19,align='center',text_inset=0))
# Exact major routing from the inspected right-panel diagram.
for id,pts in [('input-rgb',[(478,53),(497,53)]),('input-flow',[(478,103),(497,103)]),('rgb-transpose',[(585,53),(596,53)]),('flow-transpose',[(585,103),(596,103)]),('rgb-linear',[(703,53),(720,53),(720,72),(751,72)]),('flow-linear',[(703,93),(734,93),(734,121),(955,121),(955,112)]),('rgb-direct',[(703,43),(720,43),(720,16),(1005,16),(1005,207),(707,207)]),('flow-direct',[(703,114),(724,114),(724,154),(706,154)]),('linear-rgb-sum',[(831,72),(847,72),(847,55),(862,55)]),('linear-flow-sum',[(913,72),(905,72),(905,55),(884,55)]),('sum-sigmoid',[(873,66),(873,90)]),('sigmoid-compute',[(876,112),(876,127)]),('compute-flow',[(928,172),(928,178),(706,178)]),('compute-rgb',[(795,172),(795,228),(707,228)]),('flow-sum',[(578,165),(566,165),(566,177)]),('rgb-sum',[(575,224),(566,224),(566,199)]),('sum-fused',[(555,188),(549,188)]),('fused-out',[(495,191),(479,191),(479,212)])]:arrow(id,pts)
box('alpha-rgb',783,182,25,22,label='αrgb',size=15,bold=True);box('alpha-flow',866,174,30,21,label='αflow',size=15,bold=True)
text('panel-a-label','(a)',204,263,48,19,16);text('panel-b-label','(b)',714,263,48,19,16)
from math_glyph import glyph_node
for n in N:
 if n['id'] in ['mul-flow','mul-rgb','alpha-rgb','alpha-flow']:n['label']=''
text('multiply-flow-word','Multiply',581,144,48,22,14);text('multiply-flow-with','with',679,144,24,22,14);text('flow-features-label','Flow features',589,167,105,22,14)
text('multiply-rgb-word','Multiply',582,200,51,22,14);text('multiply-rgb-with','with',666,200,26,22,14);text('rgb-features-label','RGB Features',591,218,104,22,14)
N.extend([glyph_node('flow-weight',r'(1-\alpha_{\mathrm{flow}})',630,150,47,15),glyph_node('rgb-weight',r'\alpha_{\mathrm{rgb}}',637,206,26,15),glyph_node('rgb-weight-box',r'\alpha_{\mathrm{rgb}}',785,186,21,16),glyph_node('flow-weight-box',r'\alpha_{\mathrm{flow}}',867,178,28,15)])
d=dict(schema_version=1,id='robosubtasknet-figure-2',title=s['title_expected']+' — Figure 2',canvas=dict(width=1014,height=282),provenance=dict(paper_title=s['title_expected'],paper_url=s['source_url'],figure='Figure 2',page=3,license=s['license_note'],status='figure_recreation',source_sha256=s['pdf_sha256'],source_crop_pdf_points=[53,49,560,190],notes='Both panels manually reconstructed from source raster. All architecture labels, input/fusion/attention blocks, 3-D CNN boxes, Greek weights and routing are native; four compact weight expressions are editable STIX glyph outlines with retained LaTeX, not equation fields. Three separate demonstration, RGB and optical-flow frame-stack crops remain raster. Font metrics, subscript placement, perspective depths and line weights approximate source. Freeform routes lack semantic endpoint attachment.'),nodes=N,edges=[])
(out/'robosubtasknet-figure-2.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
