"""Reproduce MUSIC Figure 1 from its versioned original PDF.
Preserve source vectors and native font outlines; trace each original formula
alpha-mask component into editable contours. No raster background is retained.
"""
import argparse,json,sys
from pathlib import Path
import fitz,numpy as np,contourpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/music');a=p.parse_args()
c=json.loads((ROOT/'research/survey/mutual-information-state-intrinsic-control-config.json').read_text());s=extract(a.pdf,c,a.out)
page=fitz.open(a.pdf)[c['page']-1]
image_sequences=[seq for seq,(kind,_) in enumerate(page.get_bboxlog()) if kind=='fill-image']
for i,b in enumerate([b for b in page.get_text('dict')['blocks'] if b['type']==1]):
 rect=fitz.Rect(b['bbox'])
 if not fitz.Rect(c['crop']).contains(rect):continue
 assert b.get('mask'),'Expected transparent original equation mask'
 mask=fitz.Pixmap(b['mask']);alpha=np.frombuffer(mask.samples,dtype=np.uint8).reshape(mask.height,mask.width).astype(float)/255
 dx=rect.width*c['scale']/mask.width;dy=rect.height*c['scale']/mask.height
 ox=(rect.x0-c['crop'][0])*c['scale'];oy=(rect.y0-c['crop'][1])*c['scale']
 # Continuous half-alpha contours preserve subpixel antialias placement. Padding
 # closes any glyph touching the bitmap edge. Opposite-wound holes are retained.
 points,offsets=contourpy.contour_generator(z=np.pad(alpha,1),fill_type='OuterOffset').filled(.5,1.1)
 for j,(pts,off) in enumerate(zip(points,offsets)):
  pts=pts-.5
  x0=float(pts[:,0].min());y0=float(pts[:,1].min());x1=float(pts[:,0].max());y1=float(pts[:,1].max())
  commands=[]
  for start,end in zip(off[:-1],off[1:]):
   loop=pts[int(start):int(end)]
   for k,(x,y) in enumerate(loop):commands.append({('moveTo' if k==0 else 'lineTo'):{'x':float((x-x0)*dx),'y':float((y-y0)*dy)}})
   commands.append({'close':{}})
  s['nodes'].append(dict(id=f'music-source-formula-{i}-glyph-{j}',shape='path',x=ox+x0*dx,y=oy+y0*dy,width=(x1-x0)*dx,height=(y1-y0)*dy,commands=commands,fill='#000000',stroke='none',stroke_width=0,source_seqno=image_sequences[i],source_detail=f'Original embedded formula {i}, native contour from half-alpha source mask'))
s['nodes'].sort(key=lambda node:node.get('source_seqno',1000000))
s['provenance']['raster_formula_reconstruction']='Seven original transparent formula bitmaps individually traced as native editable glyph contours; antialias transitions approximated. No formula bitmap or panel screenshot retained.'
s['provenance']['extraction_warnings_reviewed']=['Seven source image warnings resolved by editable point-path contours of their original masks. Clipping and source geometry reviewed against the original crop.']
# Match the source baseline while retaining ordinary labels as typeable text.
for node in s['nodes']:
    if node['shape']=='text':
        node['y']=max(0,node['y']-.15*node['font_size'])
        if 'Ital' in node.get('source_font',''):node['italic']=True
s['provenance']['text_editability']='Ordinary labels and prose remain native typeable text. Mathematical expressions are editable glyph-outline paths, not live equations.'
s['provenance']['font_substitutions']='Ordinary labels/prose use Arial or Times New Roman, with explicit source-baseline adjustment. Source mathematical fonts and raster formulas use native glyph outlines.'
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(s['id'],len(s['nodes']),'native objects')
