"""Faithful ASD publisher Figure2 reconstruction with live labels and discrete source icon crops."""
import json,hashlib,fitz
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2];cid='agentic-skill-discovery';slug='asd-figure-2';D=R/'data/diagrams'/slug;A=D/'assets';A.mkdir(parents=True,exist_ok=True);pdf=R/'build/sources'/f'{cid}.pdf';doc=fitz.open(pdf);src=doc.extract_image(19);raw=D/'assets/source-icon-layer.png';raw.write_bytes(src['image']);im=Image.open(raw)
nodes=[];edges=[]
def n(id,shape,x,y,w,h,**kw):
 if 'path' in kw:
  cmds=[]
  for c in kw.pop('path'):
   keys=['x1','y1','x2','y2','x','y'] if c[0]=='cubicBezTo' else ['x','y']
   cmds.append({c[0]:dict(zip(keys,c[1:]))})
  kw['commands']=cmds
 nodes.append(dict(id=id,shape=shape,x=x,y=y,width=w,height=h,**kw))
def text(id,label,x,y,w,h,size=42,color='#000000'):n(id,'text',x,y-12,w,h,label=label,font_size=size,font_family='Arial',align='left',text_inset=0,no_wrap=True,text_color=color)
def path(id,cmds,color='#DDDDDD',sw=5):
 n(id,'path',0,0,1573,428,path=cmds,fill='none',stroke=color,stroke_width=sw)
def icon(id,b):
 crop=im.crop(b);crop.save(A/f'{id}.png');n(id,'image',b[0],b[1],b[2]-b[0],b[3]-b[1],asset=f'assets/{id}.png',alt=f'Original raster {id} icon; internal icon artwork is not editable')
n('context','path',1,8,642,414,path=[['moveTo',95,0],['lineTo',547,0],['cubicBezTo',610,0,642,35,642,100],['lineTo',642,314],['cubicBezTo',642,380,610,414,547,414],['lineTo',95,414],['cubicBezTo',32,414,0,380,0,314],['lineTo',0,100],['cubicBezTo',0,35,32,0,95,0],['close']],fill='#F9F9F9',stroke='#EEEEEE',stroke_width=4,dash=True)
# Native connector lines follow the raster original, including return curve.
path('proposal-line',[['moveTo',675,127],['lineTo',995,127]])
n('proposal-head','path',993,117,28,20,path=[['moveTo',0,0],['lineTo',28,10],['lineTo',0,20],['close']],fill='#DDDDDD',stroke='none')
path('learn-return',[['moveTo',1272,127],['lineTo',1450,127],['cubicBezTo',1612,127,1612,344,1450,344],['lineTo',1255,344]])
n('learn-head','path',1233,334,30,20,path=[['moveTo',30,0],['lineTo',0,10],['lineTo',30,20],['close']],fill='#DDDDDD',stroke='none')
path('collect-line',[['moveTo',952,344],['lineTo',687,344]])
n('collect-head','path',662,334,30,20,path=[['moveTo',30,0],['lineTo',0,10],['lineTo',30,20],['close']],fill='#DDDDDD',stroke='none')
for id,b in [('earth',(199,18,288,108)),('camera',(195,128,285,210)),('arm',(201,224,287,308)),('library',(200,315,286,399)),('llm',(692,77,791,176)),('task',(1020,0,1237,191)),('gear',(1295,71,1415,187)),('skill-options',(1010,194,1208,365)),('collect-cube',(861,299,946,390))]:icon(id,b)
n('brace','path',171,240,32,150,path=[['moveTo',29,0],['cubicBezTo',4,0,25,69,0,75],['cubicBezTo',25,81,4,150,29,150]],fill='none',stroke='#80A3CF',stroke_width=5)
for id,label,x,y,w,h,size,col in [('environment','Environment',296,40,335,66,43,'#000000'),('observations','Observations',296,145,335,64,43,'#000000'),('configuration','Configuration',296,238,340,64,43,'#000000'),('skill-library','Skill Library',296,331,340,65,43,'#000000'),('robot','Robot',29,337,133,70,43,'#000000'),('propose','Propose',790,71,209,59,40,'#777777'),('learn','Learn',1401,70,166,61,40,'#777777'),('collect','Collect',727,285,142,60,40,'#777777'),('task-label','Task',1074,106,148,66,48,'#000000'),('skills-label','Skill Options',1002,365,292,62,42,'#000000')]:text(id,label,x,y,w,h,size,col)
s=dict(schema_version=1,id=slug,title='Agentic Skill Discovery — contextual skill acquisition loop',canvas=dict(width=1573,height=428),provenance=dict(paper_title='Agentic skill discovery',paper_url='https://www2.informatik.uni-hamburg.de/wtm/publications/2026/ZWW26/1-s2.0-S0921889025003458-main.pdf',figure='Figure 2',page=4,license='CC BY4.0; https://creativecommons.org/licenses/by/4.0/',status='figure_recreation',source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),source_crop_pdf_points=[108.978,55.445,486.541,158.237],notes='Faithful structural recreation of publisher Figure2. Original icon artwork retained in nine discrete raster crops; text, context panel and three arrow routes rebuilt as native editable objects. All labels typeable. Font metrics, corner radius, brace and dash cadence approximate the original. Raster icon interiors are not editable; no complete background raster included. Original colors intentionally pale.'),nodes=nodes,edges=edges)
(D/f'{slug}.json').write_text(json.dumps(s,indent=2));doc[3].get_pixmap(matrix=fitz.Matrix(4,4),clip=fitz.Rect(108.978,55.445,486.541,158.237)).save(D/f'{slug}-original.png')
raw.unlink()
