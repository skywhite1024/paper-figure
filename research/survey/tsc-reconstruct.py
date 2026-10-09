"""Recreate original flat-raster TSC Fig2 as native editable graphical models."""
import json,fitz,math
from pathlib import Path
r=Path(__file__).resolve().parents[2];cid='transition-state-clustering-unsupervised-surgical-trajectory-segmentation-for-robot-learning';d=json.loads((r/'research/survey'/f'{cid}.json').read_text());slug='tsc-figure-2';out=r/'data/diagrams'/slug;out.mkdir(parents=True,exist_ok=True);nodes=[];edges=[]
for id,label,cx,cy in [('aS','S',106,114),('ax','x',106,258),('bS','S',404,114),('bx','x',320,258),('bt','t',490,258),('cS','S',768,114),('cx','x',618,258),('cv','v',768,258),('ct','t',922,258)]:
 nodes.append(dict(id=id,shape='ellipse',label=label,x=cx-42,y=cy-42,width=84,height=84,fill='#FFFFFF',stroke='#111111',stroke_width=1.2,font_family='Times New Roman',font_size=29,text_color='#111111',align='center',text_inset=0))
for id,label,x,w in [('title-a','Time-Invariant',10,220),('title-b','Time-Varying',300,226),('title-c','Multi-modal',685,250)]:nodes.append(dict(id=id,shape='text',label=label,x=x,y=8,width=w,height=35,font_family='Arial',font_size=28,align='left',text_inset=0,no_wrap=True,text_color='#111111'))
for src,tgt,sp,tp in [('ax','aS','top','bottom'),('bx','bS','top','bottom'),('bt','bS','top','bottom'),('bx','bt','right','left'),('cx','cS','top','left'),('cv','cS','top','bottom'),('ct','cS','top','right'),('cx','cv','right','left'),('cv','ct','right','left')]:edges.append(dict(id='e-'+src+'-'+tgt,source=src,target=tgt,source_port=sp,target_port=tp,arrow=True,stroke='#111111',stroke_width=2))
# Match diagonal source circle-boundary intersections with native paths.
by={n['id']:n for n in nodes}; diagonal={('bx','bS'),('bt','bS'),('cx','cS'),('ct','cS')}
edges=[e for e in edges if (e['source'],e['target']) not in diagonal]
for source,target in sorted(diagonal):
 a,b=by[source],by[target];ax,ay=a['x']+42,a['y']+42;bx,byy=b['x']+42,b['y']+42;dx,dy=bx-ax,byy-ay;length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
 sx,sy=ax,ay-42;ex,ey=bx-42*ux,byy-42*uy;px,py=-uy,ux
 nodes.append(dict(id='diag-'+source,shape='path',x=0,y=0,width=972,height=316,commands=[{'moveTo':{'x':sx,'y':sy}},{'lineTo':{'x':ex,'y':ey}}],fill='none',stroke='#111111',stroke_width=3.2))
 nodes.append(dict(id='head-'+source,shape='path',x=0,y=0,width=972,height=316,commands=[{'moveTo':{'x':ex,'y':ey}},{'lineTo':{'x':ex-11*ux+4*px,'y':ey-11*uy+4*py}},{'lineTo':{'x':ex-11*ux-4*px,'y':ey-11*uy-4*py}},{'close':{}}],fill='#111111',stroke='none'))
s=dict(schema_version=1,id=slug,title='Transition State Clustering graphical models',canvas=dict(width=972,height=316),provenance=dict(paper_title=d['title_expected'],paper_url=d['source_url'],figure='Figure 2',page=5,license='License not verified; private authorized reference copy',status='figure_recreation',source_sha256=d['pdf_sha256'],source_crop_pdf_points=[51,598,294,677],notes='Original three probabilistic graphical models manually recreated from flattened source image. All12 node/title labels typeable;5 dependency arrows are native attached connectors and4diagonal arrows are exact circle-boundary native paths. Font metrics and subpixel line weights approximate source. No raster backdrop.'),nodes=nodes,edges=edges)
(out/f'{slug}.json').write_text(json.dumps(s,indent=2));fitz.open(r/d['pdf_path'])[4].get_pixmap(matrix=fitz.Matrix(4,4),clip=fitz.Rect(51,598,294,677)).save(out/f'{slug}-original.png')
