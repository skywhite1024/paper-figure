"""Restore source emphasis, rotated time label and editable dataset symbols."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/dial-figure-1/dial-figure-1.json';s=json.loads(p.read_text());groups={};remove=set()
for n in s['nodes']:
 if n['shape']=='text':groups.setdefault(n['id'].rsplit('-',1)[0],[]).append(n)
for key,g in groups.items():
 if len(g)>1 and key!='pdf-text-115':
  n=g[0];n['label']=''.join(z['label'] for z in g);n['width']=max(z['x']+z['width'] for z in g)-n['x'];remove.update(z['id'] for z in g[1:])
remove.update(n['id'] for n in groups.get('pdf-text-115',[]));s['nodes']=[n for n in s['nodes'] if n['id'] not in remove]
bold=[28,30,32,34,36,38,40,42,69,71,73,76,79,80,105,109,111,113];italic=[43,44,45,46,47,49,50,52,62,63,64,65,66,68,81,82,89,90,91,92,93,94,95,96,97]
for n in s['nodes']:
 if n['shape']=='text':
  index=int(n['id'].split('-')[2]);n['no_wrap']=True
  if index in bold:n['bold']=True;n['font_size']*=.93
  if index in italic:n['italic']=True
s['nodes'].append(dict(id='time-rotated-live',shape='text',label='Time',x=1433.47,y=469.36,width=50.8,height=23.27,rotation=90,font_family='Arial',font_size=20,align='center',text_inset=0,no_wrap=True,text_color='#000000'))
for label,x in [('A',86.1949),('B',132.8682),('C',182.745)]:
 px=(x-59)*3;py=(448.288-184)*3
 s['nodes'].append(dict(id='dataset-symbol-'+label,shape='text',label='D',x=px,y=py,width=20,height=25,font_family='Times New Roman',font_size=21,italic=True,text_inset=0,no_wrap=True))
 s['nodes'].append(dict(id='dataset-subscript-'+label,shape='text',label=label,x=px+15,y=py+12,width=13,height=15,font_family='Times New Roman',font_size=11,italic=True,text_inset=0,no_wrap=True))
s['provenance']['text_repairs']='Source custom font lacked weight/style metadata; manually restored visible bold/italic emphasis, merged split ligature fragments, rebuilt rotated Time as one live textbox. Three source raster dataset symbols replaced by live italic D with letter subscripts, approximating original calligraphic glyph.'
p.write_text(json.dumps(s,indent=2))
