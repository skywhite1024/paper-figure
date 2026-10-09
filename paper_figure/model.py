"""Scene checks shared by both exporters. No inference of review approval."""
import json,math,re
from pathlib import Path
class ValidationError(ValueError):pass
def require(ok,msg):
 if not ok:raise ValidationError(msg)
def number(v,name,positive=False):
 require(type(v) in (int,float) and math.isfinite(v),f'{name}: finite number required')
 require(v>0 if positive else v>=0,f'{name}: out of range')
def text(v,name):require(isinstance(v,str) and v.strip(),f'{name}: text required')
def xml_safe(v):
 if isinstance(v,str):require(all(c in '\t\n\r' or 32<=ord(c)<=0xD7FF or 0xE000<=ord(c)<=0xFFFD or 0x10000<=ord(c)<=0x10FFFF for c in v),'XML-incompatible character')
 elif isinstance(v,dict):
  for k,x in v.items():xml_safe(k);xml_safe(x)
 elif isinstance(v,list):
  for x in v:xml_safe(x)
def local_asset(base,name):
 text(name,'asset');root=Path(base).resolve();p=(root/name).resolve()
 require(not Path(name).is_absolute() and p.is_relative_to(root),'asset must stay within scene directory')
 require(p.is_file(),'missing asset: '+name);require(p.suffix.lower() in {'.png','.jpg','.jpeg'},'PNG/JPEG required')
 magic=p.read_bytes()[:8];require(magic.startswith(b'\x89PNG\r\n\x1a\n') if p.suffix.lower()=='.png' else magic.startswith(b'\xff\xd8\xff'),'invalid image bytes')
 return p
SHAPES={'rect','rounded_rect','ellipse','diamond','text','image','path'}
PORTS={'left','right','top','bottom'}
STATUSES={'not_reviewed','in_progress','recreated','verified','blocked'}
def validate(d,base=None):
 require(isinstance(d,dict),'scene must be object');xml_safe(d)
 require(type(d.get('schema_version')) is int and d['schema_version']==1,'schema_version must be 1')
 for k in ['id','title']:text(d.get(k),k)
 require(bool(re.fullmatch('[A-Za-z0-9_-]+',d['id'])),'id must be safe slug')
 c=d.get('canvas');require(isinstance(c,dict),'canvas required')
 for k in ['width','height']:number(c.get(k),'canvas.'+k,True);require(96<=c[k]<=5000,'canvas dimension outside 96..5000')
 p=d.get('provenance');require(isinstance(p,dict),'provenance required')
 for k in ['paper_title','paper_url','license','notes']:text(p.get(k),'provenance.'+k)
 require(isinstance(p.get('status'),str) and p['status'] in {'figure_recreation','conceptual_reconstruction'},'invalid fidelity status')
 require('figure' in p and 'page' in p,'figure/page required')
 if p['status']=='figure_recreation':text(p['figure'],'figure');require(type(p['page']) is int and p['page']>0,'1-based page required')
 require(isinstance(d.get('nodes'),list) and d['nodes'],'nodes required');require(isinstance(d.get('edges'),list),'edges required')
 ids=set()
 for n in d['nodes']:
  require(isinstance(n,dict),'node must be object');text(n.get('id'),'node.id');require(n['id'] not in ids|{'0','1'},'duplicate/reserved ID');ids.add(n['id'])
  require(isinstance(n.get('shape'),str) and n['shape'] in SHAPES,'unsupported shape')
  require(isinstance(n.get('label',''),str),'label must be text')
  for k in ['x','y','width','height']:number(n.get(k),n['id']+'.'+k,k in ['width','height'])
  require(n['x']+n['width']<=c['width']+.02 and n['y']+n['height']<=c['height']+.02,'node outside canvas: '+n['id'])
  for k in ['fill','stroke','text_color']:
   if k in n:require(isinstance(n[k],str) and (n[k]=='none' or re.fullmatch('#[A-Fa-f0-9]{6}',n[k])),k+': #RRGGBB or none required')
  for k in ['font_size','stroke_width']:
   if k in n:number(n[k],k,k=='font_size')
  for k in ['bold','italic','dash']:
   if k in n:require(type(n[k]) is bool,k+': boolean required')
  for k in ['fill_opacity','stroke_opacity']:
   if k in n:number(n[k],k);require(n[k]<=1,k+' must be <=1')
  if 'align' in n:require(n['align'] in ['left','center','right'],'invalid align')
  if 'font_family' in n:require(isinstance(n['font_family'],str) and bool(re.fullmatch(r'[A-Za-z0-9 _-]+',n['font_family'])),'font_family contains unsafe style characters')
  if 'text_inset' in n:number(n['text_inset'],'text_inset')
  if 'no_wrap' in n:require(type(n['no_wrap']) is bool,'no_wrap must be boolean')
  if n['shape']=='image':
   text(n.get('asset'),'asset');text(n.get('alt'),'alt')
   if base is not None:local_asset(base,n['asset'])
  if n['shape']=='path':
   require(isinstance(n.get('commands'),list) and n['commands'],'path commands required')
   for cmd in n['commands']:
    require(isinstance(cmd,dict) and len(cmd)==1,'path command invalid');op,v=next(iter(cmd.items()))
    require(op in ['moveTo','lineTo','cubicBezTo','quadBezTo','close'] and isinstance(v,dict),'path operation invalid')
    keys={'moveTo':{'x','y'},'lineTo':{'x','y'},'cubicBezTo':{'x1','y1','x2','y2','x','y'},'quadBezTo':{'x1','y1','x','y'},'close':set()}[op]
    require(set(v)==keys,'path coordinates invalid')
    for value in v.values():require(type(value) in [int,float] and math.isfinite(value),'path coordinates must be finite')
 edgeids=set()
 for e in d['edges']:
  require(isinstance(e,dict),'edge must be object');text(e.get('id'),'edge.id');require(e['id'] not in ids|edgeids|{'0','1'},'duplicate edge ID');edgeids.add(e['id'])
  for k in ['source','target']:require(isinstance(e.get(k),str) and e[k] in ids,'unknown endpoint')
  for k in ['source_port','target_port']:require(isinstance(e.get(k,'left'),str) and e.get(k,'left') in PORTS,'invalid port')
  for k in ['arrow','dash','head_arrow']:
   if k in e:require(type(e[k]) is bool,k+': boolean required')
  if 'stroke' in e:require(isinstance(e['stroke'],str) and bool(re.fullmatch('#[A-Fa-f0-9]{6}',e['stroke'])),'edge.stroke: #RRGGBB required')
  if 'stroke_width' in e:number(e['stroke_width'],'edge.stroke_width')
  require(type(e.get('arrow',True)) is bool,'arrow must be bool');require(isinstance(e.get('label',''),str),'edge label must be text')
  require(e.get('kind','straight') in ['straight','elbow','curved'],'invalid connector kind')
  require(isinstance(e.get('waypoints',[]),list),'waypoints must be list')
  for pt in e.get('waypoints',[]):
   require(isinstance(pt,dict),'waypoint must be object')
   for k in ['x','y']:number(pt.get(k),'waypoint '+k)
   require(pt['x']<=c['width'] and pt['y']<=c['height'],'waypoint out of canvas')
 return d
def load(path):
 try:d=json.loads(Path(path).read_text(encoding='utf-8'))
 except (OSError,json.JSONDecodeError) as e:raise ValidationError(str(e)) from e
 return validate(d,Path(path).parent)
def metrics(d):
 paths=sum(n['shape']=='path' for n in d['nodes']);images=sum(n['shape']=='image' for n in d['nodes'])
 return {'native_nodes':len(d['nodes'])-images,'transparent_anchor_nodes':sum(n.get('anchor') is True or (n['shape']=='rect' and n.get('fill_opacity')==0 and n.get('stroke_opacity')==0) for n in d['nodes']),'native_freeform_paths':paths,'native_text_objects':sum(n['shape']=='text' for n in d['nodes']),'raster_images':images,'semantic_connectors':len(d['edges']),'pptx_connector_segments':sum(1+len(e.get('waypoints',[])) for e in d['edges']),'path_attachment':'freeform paths have no semantic endpoint attachment','fidelity_status':d['provenance']['status'],'visual_review':'pending'}
