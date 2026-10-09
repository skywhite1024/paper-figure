"""Use raw image objects and merge source split labels for typeable faithful text."""
import json,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];out=r/'data/diagrams/dexscale-figure-2';p=out/'dexscale-figure-2.json';s=json.loads(p.read_text());d=fitz.open(r/'build/sources/dexscale-automating-data-scaling-for-sim2real-generalizable-robot-control.pdf');ims=d[3].get_image_info(xrefs=True)
masks={t[0]:t[1] for t in d[3].get_images(full=True)}
for k,im in enumerate(ims):
 pix=fitz.Pixmap(d,im['xref']);mask=masks.get(im['xref'],0)
 if mask:pix=fitz.Pixmap(pix,fitz.Pixmap(d,mask))
 pix.save(out/f'dexscale-figure-2-raster-{k}.png')
ns={n['id']:n for n in s['nodes']};remove=set()
for inds,label in [([2,3],'Tele-'),([6,7],'Heterogeneous Data'),([11,12],'Objects'),([15,16],'Pro-'),([29,30,31],'Policy Fine-Tuning'),([34,35],'Sim2Real Deployment'),([40,41,42,43],'Obs.-Action Trajectories'),([46,47],'Imitate')]:
 g=[ns[f'pdf-text-{i}-0'] for i in inds];n=g[0];n['width']=max(a['x']+a['width'] for a in g)-n['x'];n['label']=label;remove.update(a['id'] for a in g[1:])
s['nodes']=[n for n in s['nodes'] if n['id'] not in remove]
for n in s['nodes']:
 if n['shape']=='text':n['font_size']*=.81;n['align']='center';n['no_wrap']=True
s['provenance']['text_repairs']='Source Aptos fragments merged into live complete labels and fitted Arial metrics. Raw source image objects replace rendered crops to avoid baking duplicate portions of adjacent native labels.'
p.write_text(json.dumps(s,indent=2))
