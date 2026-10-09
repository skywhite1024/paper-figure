"""Rebuild the mixed-vector ASPIRE source figure as native editable primitives.

PDF images are isolated with their original SVG clipping/masks before raster extraction.
This never replaces the whole figure by a screenshot. Font substitution is recorded.
"""
import copy,io,json,re,hashlib,subprocess,os
from pathlib import Path
import fitz
from lxml import etree as ET
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--pdf',type=Path,default=Path('/tmp/aspire.pdf'));PDF=parser.parse_args().pdf;doc=fitz.open(PDF);page=doc[1]
CROP=fitz.Rect(61,84,534,368);S=3
out=ROOT/'data/diagrams';assets=out/'assets';assets.mkdir(exist_ok=True,parents=True)
prov={'paper_title':'ASPIRE: Agentic /Skills Discovery for Robotics','paper_url':'https://arxiv.org/abs/2607.00272v1','pdf_url':'https://arxiv.org/pdf/2607.00272v1','figure':'Figure 1','page':2,'license':'arXiv page links CC BY 4.0; PDF also contains NVIDIA copyright notice. Figure-specific third-party assets not independently cleared for public redistribution. Private conversion only.','status':'figure_recreation','notes':'Original PDF vector geometry, colors and placement extracted, with individually clipped source raster assets. Original curves and zoom inset retained. Native labels use Arial/Courier New substitutions for source fonts. Freeform arrow paths remain editable points but are not semantic attached connectors. Search/code panels contain source-flattened details and remain raster unless explicitly replaced. No full-figure raster backdrop.','source_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'source_crop_pdf_points':list(CROP),'font_substitutions':{'NVIDIASans':'Arial','ArialMT':'Arial','ArialRoundedMTBold':'Arial Bold','Consolas':'Courier New','CourierNewPSMT':'Courier New'},'source_image_limit':'Image-internal text and robot/photo pixels remain raster, including small code/search snippets; native text objects reported separately.'}
d={'schema_version':1,'id':'aspire-figure-1','title':'ASPIRE Figure 1 | source-faithful reconstruction','canvas':{'width':CROP.width*S,'height':CROP.height*S+35},'provenance':prov,'nodes':[],'edges':[]}
items=[]
def col(v):return 'none' if v is None else '#'+''.join(f'{round(max(0,min(1,x))*255):02X}' for x in v[:3])
def loc(r):return {'x':(r.x0-CROP.x0)*S,'y':(r.y0-CROP.y0)*S,'width':max(r.width*S,.1),'height':max(r.height*S,.1)}
for draw in page.get_drawings():
 points=[]
 for it in draw['items']:
  if it[0] in ['l','c']:points.extend(it[1:])
  elif it[0]=='re':points.extend([it[1].tl,it[1].br])
  elif it[0]=='qu':points.extend([it[1].ul,it[1].ur,it[1].lr,it[1].ll])
 r=fitz.Rect(min(p.x for p in points),min(p.y for p in points),max(p.x for p in points),max(p.y for p in points))
 if not CROP.contains(r) or draw.get('seqno')==2:continue
 commands=[];last=None
 def pt(p):return {'x':(p.x-r.x0)*S,'y':(p.y-r.y0)*S}
 def move(p):
  global last
  if last is None or abs(last.x-p.x)+abs(last.y-p.y)>.0001:commands.append({'moveTo':pt(p)})
  last=p
 for it in draw['items']:
  if it[0]=='l':move(it[1]);commands.append({'lineTo':pt(it[2])});last=it[2]
  elif it[0]=='c':move(it[1]);a,b,c=it[2:];commands.append({'cubicBezTo':{'x1':(a.x-r.x0)*S,'y1':(a.y-r.y0)*S,'x2':(b.x-r.x0)*S,'y2':(b.y-r.y0)*S,**pt(c)}});last=c
  elif it[0]=='re':
   box=it[1];ps=[box.tl,box.tr,box.br,box.bl]
   if len(it)>2 and it[2]>0:ps=ps[::-1]
   commands.append({'moveTo':pt(ps[0])});commands.extend({'lineTo':pt(p)} for p in ps[1:]);commands.append({'close':{}});last=None
  elif it[0]=='qu':
   q=it[1];ps=[q.ul,q.ur,q.lr,q.ll];commands.append({'moveTo':pt(ps[0])});commands.extend({'lineTo':pt(p)} for p in ps[1:]);commands.append({'close':{}});last=None
  else:raise RuntimeError('Unsupported PDF path '+str(it[0]))
 if draw.get('closePath') and commands:commands.append({'close':{}})
 node={'id':f"source-path-{draw['seqno']}",'shape':'path','commands':commands,**loc(r),'fill':col(draw.get('fill')),'stroke':col(draw.get('color')),'stroke_width':float(draw.get('width') or 0)*S,'fill_opacity':draw.get('fill_opacity') if draw.get('fill_opacity') is not None else 1,'stroke_opacity':draw.get('stroke_opacity') if draw.get('stroke_opacity') is not None else 1,'dash':bool(draw.get('dashes') and draw['dashes']!='[] 0'),'source_seqno':draw['seqno']}
 items.append((draw['seqno'],node))
# Text spans remain normal editable text, using source baseline/size and local substitutions.
for span in page.get_texttrace():
 r=fitz.Rect(span['bbox'])
 if not CROP.contains(r):continue
 label=''.join(chr(c[0]) for c in span['chars']);font=span['font'];size=span['size']*S
 if not label.strip():continue
 # Native text frames use a line box; source texttrace bbox contains only font ascender/descender.
 node={'id':f"source-text-{span['seqno']}-{len(items)}",'shape':'text','label':label,**loc(r),'font_size':size,'font_family':'Courier New' if any(x in font for x in ['Courier','Consolas','Mono']) else 'Arial','bold':'Bold' in font,'italic':'Italic' in font,'text_color':col(span['color'] if isinstance(span['color'],tuple) else (0,0,0)),'align':'left','text_inset':0,'no_wrap':True,'source_font':font,'source_seqno':span['seqno']}
 items.append((span['seqno'],node))
# Isolate each image with its existing ancestor clipping and mask definitions.
svg=ET.fromstring(page.get_svg_image(text_as_path=False).encode());ns={'s':'http://www.w3.org/2000/svg'};defs=svg.find('s:defs',ns)
image_elements=[el for el in svg.iter() if el.tag.rsplit('}',1)[-1] in ['image','use'] and not any(a.tag.endswith('defs') for a in el.iterancestors())]
image_seq=[i for i,(kind,bbox) in enumerate(page.get_bboxlog()) if kind in ['fill-image','fill-shade']]
assert len(image_elements)==len(image_seq),(len(image_elements),len(image_seq))
for idx,(img,seqno) in enumerate(zip(image_elements,image_seq)):
 isolated=ET.Element(svg.tag,nsmap=svg.nsmap,**dict(svg.attrib));isolated.append(copy.deepcopy(defs))
 chain=[];parent=img.getparent()
 while parent is not None and parent is not svg:chain.append(parent);parent=parent.getparent()
 cursor=isolated
 for ancestor in reversed(chain):child=ET.Element(ancestor.tag,**dict(ancestor.attrib));cursor.append(child);cursor=child
 if img.tag.endswith('use'):
  ref=img.get('{http://www.w3.org/1999/xlink}href')[1:];resolved=svg.xpath('//*[@id=$id]',id=ref)[0];cursor.append(copy.deepcopy(resolved))
 else:cursor.append(copy.deepcopy(img))
 svgpath=ROOT/'build/isolated.svg';pngpath=ROOT/'build/isolated.png';svgpath.write_bytes(ET.tostring(isolated));subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(svgpath),str(pngpath)],check=True);png=pngpath.read_bytes()
 im=Image.open(io.BytesIO(png)).convert('RGBA');alpha=im.getchannel('A');bbox=alpha.getbbox()
 if bbox is None:continue
 r=fitz.Rect(*(x/S for x in bbox));r=r&CROP
 if r.is_empty:continue
 cropbox=(round(r.x0*S),round(r.y0*S),round(r.x1*S),round(r.y1*S));asset=f'assets/aspire-source-image-{idx:02d}.png';im.crop(cropbox).save(out/asset)
 items.append((seqno,{'id':f'source-image-{idx:02d}','shape':'image','asset':asset,'alt':f'Individually clipped ASPIRE source raster asset {idx}; internal content remains raster',**loc(r),'source_seqno':seqno}))
# Reviewed compound arrow shapes are unions, not holes. Split their subpaths
# to avoid downstream applications applying even-odd cancellation at overlaps.
fixed=[]
for seq,node in items:
 if node['shape']=='path' and seq in {33,61,73,104,106,117}:
  groups=[]
  for command in node['commands']:
   if 'moveTo' in command:groups.append([])
   groups[-1].append(command)
  for i,commands in enumerate(groups):
   piece=dict(node,id=node['id']+f'-part-{i}',commands=commands,compound_union_part=True)
   fixed.append((seq,piece))
 else:fixed.append((seq,node))
items=fixed
d['nodes']=[n for _,n in sorted(items,key=lambda x:x[0])]
overlay_path=ROOT/'research/aspire-native-snippets.json'
if overlay_path.exists():
 overlay=json.loads(overlay_path.read_text())
 removed=set(overlay['remove_source_seqnos'])
 d['nodes']=[n for n in d['nodes'] if not (n['shape']=='image' and n.get('source_seqno') in removed)]
 d['nodes'].extend(overlay['nodes']);d['edges'].extend(overlay['edges'])
 d['provenance']['notes']=d['provenance']['notes'].replace('Search/code panels contain source-flattened details and remain raster unless explicitly replaced.','Code and evolutionary-search panels manually reconstructed as native text/shapes/connections from original pixels; typography and small routing differences remain.')
 d['provenance']['source_image_limit']='Only individual photos, diagnostic image pixels and decorative logo assets remain raster; the code/search mini-panels are native reconstructions.'
 d['provenance']['snippet_notes']=overlay.get('notes','')
 d['provenance']['native_snippet_reconstruction']='Source code/search images replaced by native editable labels, boxes and arrows; original information and relative arrangement retained with small geometric/font approximation.'
d['nodes'].append({'id':'attribution','shape':'text','label':'Lu et al., ASPIRE (2026), Fig. 1, p. 2 · Original vector paths + editable text; source photos/snippets remain separate raster assets','x':0,'y':CROP.height*S+6,'width':CROP.width*S,'height':24,'font_size':14,'text_color':'#444444','align':'center'})
(out/'aspire-figure-1.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
page.get_pixmap(matrix=fitz.Matrix(S,S),clip=CROP).save(ROOT/'build/aspire-original.png')
print('Extracted',len(d['nodes']),'native path/text/image objects')
