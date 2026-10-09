"""Recover v0.1 graph from the preserved editable draw.io deliverables."""
import base64,json,re,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for source in (root/'build/recovered').glob('*.drawio'):
 tree=ET.parse(source); doc=tree.getroot(); page=doc.find('diagram'); graph=page.find('mxGraphModel')
 scene={'schema_version':1,'id':page.get('id'),'title':page.get('name'),'canvas':{'width':float(graph.get('pageWidth')),'height':float(graph.get('pageHeight'))},'provenance':json.loads(doc.get('paper-figure-provenance')),'nodes':[],'edges':[]}
 for c in graph.findall('root/mxCell'):
  raw=c.get('style',''); st=dict(item.split('=',1) for item in raw.split(';') if '=' in item);g=c.find('mxGeometry')
  if c.get('vertex')=='1':
   shape='rect'
   for token,name in [('text;','text'),('ellipse;','ellipse'),('rhombus;','diamond'),('rounded=1;','rounded_rect'),('shape=image;','image')]:
    if token in raw:shape=name
   n={'id':c.get('id'),'label':c.get('value',''),'shape':shape,**{k:float(g.get(k)) for k in ['x','y','width','height']}}
   for a,b in [('fillColor','fill'),('strokeColor','stroke'),('fontColor','text_color')]:
    if st.get(a,'').startswith('#'):n[b]=st[a]
   n['font_size']=float(st.get('fontSize',20));n['dash']=st.get('dashed')=='1'
   if shape=='image':
    fmt,encoded=st['image'].split(',',1);ext='png' if 'png' in fmt else 'jpg';asset=Path('assets')/f"{scene['id']}-{n['id']}.{ext}";dest=root/'data/diagrams/legacy'/asset;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(base64.b64decode(encoded));n.update(asset=str(asset),alt='Recovered original source photo panel')
   scene['nodes'].append(n)
  elif c.get('edge')=='1':
   ports={(0,.5):'left',(1,.5):'right',(.5,0):'top',(.5,1):'bottom'}
   e={'id':c.get('id'),'source':c.get('source'),'target':c.get('target'),'label':c.get('value',''),'arrow':st.get('endArrow')!='none','stroke':st.get('strokeColor','#475569'),'source_port':ports.get((float(st.get('exitX',1)),float(st.get('exitY',.5))),'right'),'target_port':ports.get((float(st.get('entryX',0)),float(st.get('entryY',.5))),'left'),'waypoints':[{'x':float(p.get('x')),'y':float(p.get('y'))} for p in g.findall('Array/mxPoint')]}
   scene['edges'].append(e)
 dest=root/'data/diagrams/legacy'/f"{scene['id']}-v0.1.json";dest.write_text(json.dumps(scene,ensure_ascii=False,indent=2)+'\n')
 print(dest)
