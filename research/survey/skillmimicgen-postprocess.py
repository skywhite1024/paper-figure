"""Clip source photo objects while preserving all native overlaid labels and motion paths."""
import json,fitz,io
from PIL import Image
from pathlib import Path
r=Path(__file__).resolve().parents[2];out=r/'data/diagrams/skillmimicgen-figure-1';p=out/'skillmimicgen-figure-1.json';s=json.loads(p.read_text());d=fitz.open(r/'build/sources/skillmimicgen-automated-demonstration-generation-for-efficient-skill-learning-and-deployment.pdf');ims=d[1].get_image_info(xrefs=True);assets=out/'assets';assets.mkdir(exist_ok=True)
clips=[[164.088,92.90365,227.29901,163.24875],[261.48419,97.57839,301.32809,141.8494],[328.87448,97.57839,368.71841,141.8494],[429.22211,89.216095,493.1691,160.0497]]
for k,(im,b,q) in enumerate(zip(ims,clips,[80,85,90,95])):
 raw=d.extract_image(im['xref']);a=Image.open(io.BytesIO(raw['image']));x0,y0,x1,y1=im['bbox'];box=((b[0]-x0)/(x1-x0)*a.width,(b[1]-y0)/(y1-y0)*a.height,(b[2]-x0)/(x1-x0)*a.width,(b[3]-y0)/(y1-y0)*a.height);asset=f'assets/source-photo-{k}.png';a.crop(box).save(out/asset)
 s['nodes'].append(dict(id=f'source-photo-{k}',shape='image',asset=asset,alt='Original robot photo with native overlays preserved separately',x=(b[0]-108)*4,y=(b[1]-72)*4,width=(b[2]-b[0])*4,height=(b[3]-b[1])*4,source_seqno=q))
s['nodes'].sort(key=lambda n:n.get('source_seqno',0))
for n in s['nodes']:
 if n['id']=='pdf-path-82':n['stroke_width']=4.0
 if n['shape']=='text':n['font_size']*=.9;n['no_wrap']=True
s['provenance']['stroke_repair']='PDF extraction reported an impossible 152400-scene-pixel red initiation stroke; restored source visually measured 4px line width.'
s['provenance']['image_repairs']='Raw source PDF image objects cropped to original PDF clipping bounds; original Initiation/Demo/Adapt/MP/BC labels and drawn motion paths remain independently editable above the photos.'
p.write_text(json.dumps(s,indent=2))
