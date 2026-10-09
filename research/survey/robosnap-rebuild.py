"""Reproduce this inspected paper figure with live labels and native PDF geometry.
Original raster image/shading objects are isolated individually with their source
SVG transforms, clipping and alpha. No full-figure image is used as a backdrop.
"""
import json,hashlib,subprocess,sys,copy,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from lxml import etree
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from paper_figure.pdf_extract import extract
from research.prepare_candidate import prepare
SLUG='robosnap';CAT='robosnap-one-shot-real-to-sim-scene-generation-for-generalizable-robot-learning-and-evaluation'
evpath=R/'research/survey'/f'{CAT}.json';ev=json.loads(evpath.read_text());pdf=R/ev['pdf_path'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(pdf)==ev['pdf_sha256']
D=R/'data/diagrams'/SLUG;B=R/'build'/SLUG;B.mkdir(parents=True,exist_ok=True);C=R/'build/candidates'/SLUG
cfg=json.loads((R/'research/survey'/f'{SLUG}-config.json').read_text());s=extract(pdf,cfg,D);scene=D/(s['id']+'.json');page=fitz.open(pdf)[cfg['page']-1];crop=fitz.Rect(cfg['crop']);sc=cfg['scale'];nodes=s['nodes'];logs=page.get_bboxlog()
# Original raster assets are not rectangular screenshots: preserve exact source clips.
svg=etree.fromstring(page.get_svg_image(text_as_path=True).encode(),etree.XMLParser(recover=True));tag=lambda e:e.tag.rsplit('}',1)[-1]
ids={e.get('id') for e in svg.iter() if tag(e)=='image'}
instances=[e for e in svg.iter() if (tag(e)=='image' or tag(e)=='use' and e.get('{http://www.w3.org/1999/xlink}href','')[1:] in ids) and not any(tag(a)=='defs' for a in e.iterancestors())]
image_logs=[(seq,fitz.Rect(bb)) for seq,(kind,bb) in enumerate(logs) if kind in ('fill-image','fill-shade')]
assert len(instances)==len(image_logs),(len(instances),len(image_logs))
jobs=[]
for i,(element,(seq,box)) in enumerate(zip(instances,image_logs)):
 if not box.intersects(crop):continue
 if i in cfg.get('skip_raster_indices',[]):continue
 if any(fitz.Rect(r['bbox']).contains(box & crop) for r in cfg.get('raster_regions',[])):continue
 iso=copy.deepcopy(svg);allinst=[e for e in iso.iter() if (tag(e)=='image' or tag(e)=='use' and e.get('{http://www.w3.org/1999/xlink}href','')[1:] in ids) and not any(tag(a)=='defs' for a in e.iterancestors())];target=allinst[i]
 for e in list(iso.iter()):
  if e is iso or any(tag(a)=='defs' for a in e.iterancestors()) or tag(e) in ('svg','defs','g','mask','clipPath'):continue
  if e is not target and e.getparent() is not None:e.getparent().remove(e)
 iso.set('viewBox',' '.join(map(str,cfg['crop'][:2]+[crop.width,crop.height])));iso.set('width',str(crop.width*sc));iso.set('height',str(crop.height*sc))
 fn=B/f'isolated-raster-{i}.svg';fn.write_bytes(etree.tostring(iso));jobs.append([str(fn),str(B/f'isolated-raster-{i}.png'),i,seq])
js="const fs=require('fs'),sharp=require('sharp'); (async()=>{for(const j of JSON.parse(fs.readFileSync(process.argv[1]))){await sharp(fs.readFileSync(j[0])).png().toFile(j[1]);}})().catch(e=>{console.error(e);process.exit(1)});"
(B/'raster-jobs.json').write_text(json.dumps(jobs));subprocess.run(['node','-e',js,str(B/'raster-jobs.json')],check=True,cwd=R)
for _,png,i,seq in jobs:
 im=Image.open(png).convert('RGBA');box=im.getchannel('A').getbbox()
 if not box:continue
 name=f'{SLUG}-source-raster-{i}.png';im.crop(box).save(D/name)
 nodes.append({'id':f'source-raster-{i}','shape':'image','label':'','asset':name,'alt':'Isolated original photo/rendering/icon/shading asset; original source transparency and clip retained; internal pixels remain raster','x':box[0],'y':box[1],'width':box[2]-box[0],'height':box[3]-box[1],'source_seqno':seq})
s['nodes']=sorted(nodes,key=lambda n:n.get('source_seqno',100000))
# PAPER_SPECIFIC_POSTPROCESS
for n in s['nodes']:
 if n.get('stroke_width',0)>100:n['stroke_width']/=25400
s['provenance']['notes']+=' Source EMU-like stroke width anomaly corrected by25400 against source pixel evidence.'

for n in s['nodes']:
 if n['shape']=='text':
  n['bold']=n.get('bold',False) or any(x in n.get('source_font','') for x in ('Black','Heavy','ExtraBold'))
  n['label']=n['label'].replace('ﬁ','fi')
  font=('tibo' if n.get('bold') else 'tiro') if n.get('font_family')=='Times New Roman' else ('hebo' if n.get('bold') else 'helv');length=fitz.get_text_length(n['label'],fontname=font,fontsize=n['font_size'])
  if length>n['width']:n['font_size']*=n['width']/length*.97

s['provenance']['notes']+=' Original raster assets isolated with their exact original alpha, clipping and affine transforms; no full-figure raster backdrop.'
s['provenance']['original_extraction_warnings']=s['provenance'].get('extraction_warnings',[])
s['provenance']['extraction_warnings']=[w for w in s['provenance'].get('extraction_warnings',[]) if not w.startswith('unhandled image/shading')]
s['provenance']['raster_boundaries']=[{'id':n['id'],'bounds_canvas':[n[k] for k in ['x','y','width','height']],'detail':n['alt']} for n in s['nodes'] if n['shape']=='image']
scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(B),'--preview','--force'],cwd=R,check=True)
prepare(SLUG,evpath,scene,B,D/(s['id']+'-original.png'))
with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
v={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source inspected; generated preview comparison pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(n.get('label')) for n in s['nodes']),'native_paths':sum(n['shape']=='path' for n in s['nodes']),'raster_images':sum(n['shape']=='image' for n in s['nodes']),'raster_boundaries':s['provenance']['raster_boundaries']},'limitations':['Native geometry retained; font metrics, dashes, arrow rendering may vary','Native paths are editable but lack automatic semantic attachment','No PowerPoint or draw.io GUI editing validation claimed']}
(C/'VALIDATION.json').write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');print(SLUG,counts)
