"""Retain exact original source image objects without rasterizing nearby live labels."""
import json,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];out=r/'data/diagrams/gsc-figure-3';p=out/'gsc-figure-3.json';s=json.loads(p.read_text());d=fitz.open(r/'build/sources/generative-skill-chaining-long-horizon-skill-planning-with-diffusion-models.pdf');images=[];a=out/'assets';a.mkdir(exist_ok=True)
for k,im in enumerate(d[4].get_image_info(xrefs=True)):
 pix=fitz.Pixmap(d,im['xref']);asset='assets/source-robot-'+str(k)+'.png';pix.save(out/asset);x0,y0,x1,y1=im['bbox'];images.append(dict(id='source-robot-'+str(k),shape='image',asset=asset,alt='Original robot skill example rendering '+str(k+1),x=(x0-108)*4,y=(y0-70)*4,width=(x1-x0)*4,height=(y1-y0)*4))
texts=[n for n in s['nodes'] if n['shape']=='text'];s['nodes']=[n for n in s['nodes'] if n['shape']!='text']+images+texts
for n in texts:n['font_size']*=.90;n['align']='center';n['no_wrap']=True
s['provenance']['image_repairs']='Eight source raster objects extracted directly by PDF xref without surrounding captions. Original full image bounds retained and all external captions remain live text; this avoids duplicating captions in rendered crops.'
p.write_text(json.dumps(s,indent=2))
