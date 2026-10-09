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
SLUG='vlbiman';CAT='vlbiman-vision-language-anchored-one-shot-demonstration-enables-generalizable-bimanual-robotic-manipulation'
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
# The original uses Arial Narrow. Use an available native narrow face
# and source-width fitting rather than letting regular Arial overflow panels.
fontreg=fitz.Font(fontfile='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Regular.otf');fontbold=fitz.Font(fontfile='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf')
for n in s['nodes']:
 if n['shape']=='text':
  n['font_family']='Nimbus Sans Narrow';f=fontbold if n.get('bold') else fontreg;length=f.text_length(n['label'],fontsize=n['font_size'])
  if length>n['width']:n['font_size']*=n['width']/length*.98
# Rebuild the source header strip whose shape crosses the source crop boundary.
header={'id':'stage-header-arrow','shape':'path','label':'','x':9,'y':1,'width':1172,'height':49,'fill':'#D9D9D9','stroke':'none','commands':[{'moveTo':{'x':0,'y':9}},{'lineTo':{'x':1114,'y':9}},{'lineTo':{'x':1114,'y':0}},{'lineTo':{'x':1172,'y':24}},{'lineTo':{'x':1114,'y':49}},{'lineTo':{'x':1114,'y':38}},{'lineTo':{'x':0,'y':38}},{'close':{}}]}
s['nodes'].insert(0,header)
for j,(label,x,w) in enumerate([('1. Task-Aware Demonstration Decomposition',99,405),('2. VLM-based Adaptation',630,226),('3. Trajectory Composition',922,227)]):
 s['nodes'].append({'id':f'stage-title-{j}','shape':'text','label':label,'x':x,'y':8,'width':w,'height':33,'font_size':23,'font_family':'Nimbus Sans Narrow','bold':True,'text_color':'#4B4B4B','align':'left','text_inset':0,'no_wrap':True})


# Some original object masks are unsupported by SVG rasterization. Recombine
# the original PDF image and its own alpha mask without screenshotting labels.
blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1]
for idx in [25,26,29,30]:
 s['nodes']=[n for n in s['nodes'] if n['id']==f'source-raster-{idx}' and False or n['id']!=f'source-raster-{idx}']
 b=blocks[idx];pix=fitz.Pixmap(b['image'])
 if b.get('mask'):
  if pix.alpha:pix=fitz.Pixmap(pix,0)
  pix=fitz.Pixmap(pix,fitz.Pixmap(b['mask']))
 name=f'{SLUG}-alpha-photo-{idx}.png';pix.save(D/name);box=fitz.Rect(b['bbox'])
 n={'id':f'alpha-photo-{idx}','shape':'image','label':'','asset':name,'alt':'Original isolated masked bottle/cup photo; original PDF image and its own alpha recombined','x':(box.x0-crop.x0)*sc,'y':(box.y0-crop.y0)*sc,'width':box.width*sc,'height':box.height*sc}
 # Above the panel's base photo, below the text and overlay arrow annotations.
 s['nodes'].insert(next((j for j,v in enumerate(s['nodes']) if v.get('source_seqno',100000)>image_logs[idx][0]),len(s['nodes'])),n)
# Width-fit ordinary labels using the actual broadly available native face.
for n in s['nodes']:
 if n['shape']=='text':
  n['font_family']='Arial';font='hebo' if n.get('bold') else 'helv';length=fitz.get_text_length(n['label'],fontname=font,fontsize=n['font_size'])
  if length>n['width']*.94:n['font_size']*=n['width']*.94/length
# Explicit complete phrases keep colored terms separated even when a text
# renderer trims a leading/trailing space in a separate source font span.
seqgroups=[[28,29,30],[33],[35,36,38,39],[94,95,96,97],[98,99,100],[166,167,168],[169,170,171],[203,204,205],[207,208,209,210,211],[212,213]]
newlines=[('Binocular Observation (showing left RGB)',113.91,248.3,90.53,6.3,'#FFFFFF'),('Pour water from',164.51,199.72,38.56,6.41,'#000000'),('bottle into cup.',166.1,207.37,34.3,6.41,'#000000'),('※ For new instances / geometries',311.45,150.0,88,7.4,'#000000'),('※ For changed spatial location',315.39,102,80,7.1,'#000000'),('※ For changed spatial location',417.04,114.6,74,7,'#000000'),('※ For new instances / geometries',413.59,156.1,81,7,'#000000'),('Just adjust grasp actions of two arms!',411.6,143.91,84,6.12,'#000000'),('First adjust grasp / place actions, then',411.32,185.26,86,6.12,'#000000'),('align dual-arm coordination to pour.',414.11,192.56,79,6.12,'#000000')]
remove={q for group in seqgroups for q in group};s['nodes']=[n for n in s['nodes'] if n.get('source_seqno') not in remove or n['shape']!='text']
for li,(label,x,y,w,h,color) in enumerate(newlines):
 fs=min(h*sc,w*sc*.94/fitz.get_text_length(label,fontname='helv',fontsize=1))
 if li in [2,7,8,9]:
  import re
  words=label.split(' ');offset=0;lengths=[fitz.get_text_length(t,fontname='helv',fontsize=fs) for t in words];gap=(w*sc*.97-sum(lengths))/max(1,len(words)-1)
  for wi,(word,leng) in enumerate(zip(words,lengths)):
   col='#008000' if word in ('grasp','place','align') else color
   s['nodes'].append({'id':f'phrase-{li}-{wi}','shape':'text','label':word,'x':(x-crop.x0)*sc+offset,'y':(y-crop.y0)*sc,'width':leng+1,'height':h*sc,'font_size':fs,'font_family':'Arial','text_color':col,'align':'left','text_inset':0,'no_wrap':True});offset+=leng+gap
 else:s['nodes'].append({'id':f'phrase-{li}','shape':'text','label':label,'x':(x-crop.x0)*sc,'y':(y-crop.y0)*sc,'width':w*sc,'height':h*sc,'font_size':fs,'font_family':'Arial','text_color':color,'align':'left','text_inset':0,'no_wrap':True})
s['provenance']['notes']+=' Source Arial Narrow is approximated with source-width-fitted native Arial to avoid application font substitution overflow; all text remains live.'

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
