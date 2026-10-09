import base64,hashlib,json,os,shutil,subprocess,tempfile,zlib
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import quote
from .model import require,ValidationError,local_asset,metrics,dash_style,load
PORT={'left':(0,.5),'right':(1,.5),'top':(.5,0),'bottom':(.5,1)}
def drawio_dash(value, default_width):
 style=dash_style(value)
 if style=='solid':return 'dashed=0;'
 result='dashed=1;'
 pattern=value.get('dash_pattern')
 if pattern:
  # mxGraph dashPattern entries are multiples of the rendered stroke width.
  width=value.get('stroke_width',default_width) or 1
  pattern=[length/width for length in pattern]
 else:
  pattern={'dashed':[3,3],'dotted':[1,1],'dash-dot':[3,2,1,2],'dash-dot-dot':[3,2,1,2,1,2]}[style]
 return result+'dashPattern='+' '.join(format(length,'.12g') for length in pattern)+';'
def stencil(n):
 s=ET.Element('shape',name=n['id'],w=str(n['width']),h=str(n['height']),aspect='variable',strokewidth='inherit');fg=ET.SubElement(s,'foreground');path=ET.SubElement(fg,'path')
 for cmd in n['commands']:
  op,v=next(iter(cmd.items()));v=dict(v)
  if op=='cubicBezTo':v['x3']=v.pop('x');v['y3']=v.pop('y')
  if op=='quadBezTo':v['x2']=v.pop('x');v['y2']=v.pop('y')
  ET.SubElement(path,{'moveTo':'move','lineTo':'line','cubicBezTo':'curve','quadBezTo':'quad','close':'close'}[op],**{k:str(x) for k,x in v.items()})
 ET.SubElement(fg,'fillstroke' if n.get('fill','none')!='none' and n.get('stroke','none')!='none' else ('fill' if n.get('fill','none')!='none' else 'stroke'))
 raw=quote(ET.tostring(s,encoding='unicode'),safe="~()*!.'-").encode(); compressor=zlib.compressobj(wbits=-15)
 return base64.b64encode(compressor.compress(raw)+compressor.flush()).decode()
def drawio(d,out,base):
 doc=ET.Element('mxfile',host='app.diagrams.net',agent='paper-figure',**{'paper-figure-provenance':json.dumps(d['provenance'],ensure_ascii=False)})
 pg=ET.SubElement(doc,'diagram',id=d['id'],name=d['title']);g=ET.SubElement(pg,'mxGraphModel',page='1',pageScale='1',pageWidth=str(d['canvas']['width']),pageHeight=str(d['canvas']['height']));r=ET.SubElement(g,'root');ET.SubElement(r,'mxCell',id='0');ET.SubElement(r,'mxCell',id='1',parent='0')
 for n in d['nodes']:
  shape={'rect':'rounded=0','rounded_rect':'rounded=1;arcSize=12','ellipse':'ellipse','diamond':'rhombus','text':'text','image':'shape=image','path':'shape=stencil('+stencil(n)+')' if n['shape']=='path' else ''}[n['shape']]
  fill='none' if n['shape']=='text' else n.get('fill','#FFFFFF');stroke='none' if n['shape']=='text' else n.get('stroke','#334155')
  style=f"{shape};html=0;whiteSpace={'nowrap' if n.get('no_wrap') else 'wrap'};fillColor={fill};strokeColor={stroke};strokeWidth={n.get('stroke_width',1.5)};fontColor={n.get('text_color','#111111')};fontSize={n.get('font_size',20)};fontFamily={n.get('font_family','Arial')};fontStyle={(1 if n.get('bold') else 0)+(2 if n.get('italic') else 0)};align={n.get('align','center')};verticalAlign=middle;spacing={n.get('text_inset',0)};{drawio_dash(n,1.5)}fillOpacity={100*n.get('fill_opacity',1)};strokeOpacity={100*n.get('stroke_opacity',1)};"
  if n.get('rotation'):style+=f"rotation={n['rotation']};"
  if n['shape']=='image':
   p=local_asset(base,n['asset']);mime='image/png' if p.suffix.lower()=='.png' else 'image/jpeg';style+=f"image=data:{mime},{base64.b64encode(p.read_bytes()).decode()};imageAspect=0;"
  cell=ET.SubElement(r,'mxCell',id=n['id'],value='' if n['shape']=='image' else n.get('label',''),style=style,vertex='1',parent='1')
  ET.SubElement(cell,'mxGeometry',**{k:str(n[k]) for k in ['x','y','width','height']},**{'as':'geometry'})
 for e in d['edges']:
  a=PORT[e.get('source_port','right')];b=PORT[e.get('target_port','left')]
  st=f"html=0;endArrow={'block' if e.get('arrow',True) else 'none'};strokeColor={e.get('stroke','#475569')};strokeWidth={e.get('stroke_width',2)};exitX={a[0]};exitY={a[1]};entryX={b[0]};entryY={b[1]};fontSize=16;startArrow={'block' if e.get('head_arrow',False) else 'none'};{drawio_dash(e,2)}"
  if e.get('kind')=='elbow':st+='edgeStyle=orthogonalEdgeStyle;'
  if e.get('kind')=='curved':st+='curved=1;edgeStyle=orthogonalEdgeStyle;'
  c=ET.SubElement(r,'mxCell',id=e['id'],value=e.get('label',''),style=st,edge='1',parent='1',source=e['source'],target=e['target']);geom=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
  if e.get('waypoints'):
   arr=ET.SubElement(geom,'Array',**{'as':'points'})
   for pt in e['waypoints']:ET.SubElement(arr,'mxPoint',x=str(pt['x']),y=str(pt['y']))
 ET.indent(doc);ET.ElementTree(doc).write(out,encoding='utf-8',xml_declaration=True)
def pptx(d,out,base,preview):
 node=os.getenv('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node');mods=os.getenv('CODEX_PRIMARY_RUNTIME_NODE_MODULES') or os.getenv('PAPER_FIGURE_NODE_MODULES');require(node and mods,'PPTX requires Node.js and separately available @oai/artifact-tool runtime')
 with tempfile.TemporaryDirectory(prefix='paper-figure-') as tmp:
  t=Path(tmp);(t/'node_modules').symlink_to(Path(mods),target_is_directory=True);shutil.copyfile(Path(__file__).with_name('pptx_export.mjs'),t/'export.mjs');(t/'input.json').write_text(json.dumps(dict(d,asset_base=str(Path(base).resolve()),output=str(Path(out).resolve()),preview=preview)))
  try:r=subprocess.run([node,str(t/'export.mjs'),str(t/'input.json')],capture_output=True,text=True,timeout=240)
  except (OSError,subprocess.TimeoutExpired) as exc:raise ValidationError(str(exc)) from exc
  require(r.returncode==0,'PPTX backend: '+r.stderr[-2500:]);Path(str(out)+'.inspect.ndjson').unlink(missing_ok=True)
def input_hashes(d,source):
 source=Path(source)
 assets=sorted({n['asset'] for n in d['nodes'] if n['shape']=='image'})
 return {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'assets':[{'name':name,'sha256':hashlib.sha256(local_asset(source.parent,name).read_bytes()).hexdigest()} for name in assets]}
def export(d,source,out,formats=('drawio','pptx'),force=False,preview=False):
 inputs=input_hashes(d,source)
 snapshot=load(source)
 require(snapshot==d,'In-memory scene differs from source JSON; reload before export')
 d=snapshot
 out=Path(out);require(formats and all(f in ['drawio','pptx'] for f in formats),'unsupported format');names=[d['id']+'.'+f for f in formats]+[d['id']+'.manifest.json']+([d['id']+'.png'] if preview and 'pptx' in formats else [])
 require(force or not any((out/n).exists() for n in names),'output exists; use --force');out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=out,prefix='.stage-') as tmp:
  t=Path(tmp)
  for fmt in formats:
   target=t/(d['id']+'.'+fmt)
   if fmt=='drawio':drawio(d,target,Path(source).parent)
   else:pptx(d,target,Path(source).parent,preview)
  require(input_hashes(d,source)==inputs,'Source JSON or raster asset changed during export; outputs not published')
  manifest={'schema_version':1,'diagram_id':d['id'],**inputs,'provenance':d['provenance'],'metrics':metrics(d),'files':[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(t.iterdir())]}
  (t/(d['id']+'.manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  for p in t.iterdir():os.replace(p,out/p.name)
 return manifest
