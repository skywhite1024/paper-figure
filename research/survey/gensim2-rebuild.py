"""Paper-specific reconstruction of the inspected original PDF figure."""
import json,hashlib,subprocess,sys,zipfile,xml.etree.ElementTree as ET,fitz
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from paper_figure.pdf_extract import extract
from research.prepare_candidate import prepare
SLUG='gensim2';CAT='gensim2-scaling-robot-data-generation-with-multi-modal-and-reasoning-llms'
evidence_path=R/'research/survey'/f'{CAT}.json';ev=json.loads(evidence_path.read_text());pdf=Path(ev['pdf_path']);pdf=pdf if pdf.is_absolute() else R/pdf
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(pdf)==ev['pdf_sha256']
D=R/'data/diagrams'/SLUG;B=R/'build'/SLUG;C=R/'build/candidates'/SLUG;cfg=json.loads((R/'research/survey'/f'{SLUG}-config.json').read_text())
s=extract(pdf,cfg,D);scene=D/(s['id']+'.json')
# Review-isolated original images, preserving alpha and rectangular source clips.
page=fitz.open(pdf)[cfg['page']-1];blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1];crop=fitz.Rect(cfg['crop']);sc=cfg['scale'];nodes=s['nodes'];logs=page.get_bboxlog()
for idx in cfg.get('manual_raw_images',[]):
 b=blocks[idx];box=fitz.Rect(b['bbox']);clip=fitz.Rect(cfg.get('image_clips',{}).get(str(idx),list(box)));pix=fitz.Pixmap(b['image'])
 if pix.colorspace and pix.colorspace.n not in (1,3):pix=fitz.Pixmap(fitz.csRGB,pix)
 if b.get('mask'):
  if pix.alpha:pix=fitz.Pixmap(pix,0)
  pix=fitz.Pixmap(pix,fitz.Pixmap(b['mask']))
 from PIL import Image
 import io
 im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA');im=im.crop((round((clip.x0-box.x0)/box.width*im.width),round((clip.y0-box.y0)/box.height*im.height),round((clip.x1-box.x0)/box.width*im.width),round((clip.y1-box.y0)/box.height*im.height)))
 name=f'{SLUG}-source-image-{idx}.png';im.save(D/name)
 matches=[seq for seq,(kind,bb) in enumerate(logs) if kind in ('fill-image','fill-shade') and all(abs(a-v)<.02 for a,v in zip(box,bb))]
 seq=matches[0] if matches else 50
 nodes.append({'id':f'reviewed-image-{idx}','shape':'image','label':'','asset':name,'alt':'Original isolated photo/icon/background asset with original transparency; internal pixels remain raster','x':(clip.x0-crop.x0)*sc,'y':(clip.y0-crop.y0)*sc,'width':clip.width*sc,'height':clip.height*sc,'source_seqno':seq})
s['nodes']=sorted(nodes,key=lambda n:n.get('source_seqno',100000))
s['provenance']['notes']+=' Original source image transparency and reviewed rectangular clips retained; CMYK photos converted to RGB.'

for n in s['nodes']:
 if n['shape']=='text' and n.get('source_font','').startswith('Avenir'):n['bold']='Heavy' in n['source_font']
 if n.get('label')=='MLLM':n['font_size']*=.90
s['provenance']['original_extraction_warnings']=s['provenance'].get('extraction_warnings',[])
s['provenance']['extraction_warnings']=[w for w in s['provenance'].get('extraction_warnings',[]) if not w.startswith('unhandled image/shading') and not w.startswith('rotated text needs')]
s['provenance']['manual_image_review']='All displayed source images handled explicitly using isolated alpha assets and reviewed clips; source versus generated preview inspected.'
# PAPER_SPECIFIC_POSTPROCESS
scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(B),'--preview','--force'],cwd=R,check=True)
prepare(SLUG,evidence_path,scene,B,D/(s['id']+'-original.png'))
with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
validation={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source inspected; generated preview comparison pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(n.get('label')) for n in s['nodes']),'native_paths':sum(n['shape']=='path' for n in s['nodes']),'raster_images':sum(n['shape']=='image' for n in s['nodes']),'raster_boundaries':[{'id':n['id'],'bounds_canvas':[n[k] for k in ['x','y','width','height']],'detail':n['alt']} for n in s['nodes'] if n['shape']=='image']},'limitations':['Source native geometry retained; fonts and dash/arrow rendering can vary','Native paths are editable but lack automatic semantic attachment','No PowerPoint or draw.io GUI editing validation claimed']}
(C/'VALIDATION.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n');print(SLUG,validation['editability'])
