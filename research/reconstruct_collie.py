"""Reconstruct the inspected COLLIE Figure 1 with native ordinary labels.
Separate original images retain their affine transforms and source masks. Tiny
latent gradient dots additionally use their original Bezier clipping contours.
"""
import argparse,json,sys,math,io
from pathlib import Path
import fitz,numpy as np
from PIL import Image,ImageDraw,ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/collie');a=p.parse_args()
c=json.loads((ROOT/'research/survey/collie-guiding-skill-discovery-in-semantically-coherent-latent-space-config.json').read_text());s=extract(a.pdf,c,a.out)
page=fitz.open(a.pdf)[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1]
paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
assert len(blocks)==len(paints)==75
frame=fitz.Rect(55.439998626708984,67.06085205078125,541.424560546875,162.64097595214844)
clips=[d for d in page.get_drawings(extended=True) if d['type']=='clip' and len(d['items'])==4 and all(item[0]=='c' for item in d['items']) and fitz.Rect(d['scissor']).width<10 and fitz.Rect(d['scissor']).height<10]
assert len(clips)==17
for i,(block,(seq,kind,_)) in enumerate(zip(blocks,paints)):
    rect=fitz.Rect(block['bbox'])&crop&frame
    if rect.is_empty:continue
    pix=fitz.Pixmap(block['image'])
    if block.get('mask'):
        if pix.alpha:pix=fitz.Pixmap(pix,0)
        pix=fitz.Pixmap(pix,fitz.Pixmap(block['mask']))
    im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA')
    # Render this single source component in its page-space bounding box.
    # Repeated shadows, flags and robot poses remain independent objects.
    output_scale=6
    w=max(1,math.ceil(rect.width*output_scale));h=max(1,math.ceil(rect.height*output_scale))
    aa,bb,cc,dd,ee,ff=block['transform'];det=aa*dd-bb*cc
    affine=(im.width*dd*rect.width/w/det,-im.width*cc*rect.height/h/det,im.width*(dd*(rect.x0-ee)-cc*(rect.y0-ff))/det,
            -im.height*bb*rect.width/w/det,im.height*aa*rect.height/h/det,im.height*(-bb*(rect.x0-ee)+aa*(rect.y0-ff))/det)
    im=im.transform((w,h),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC)
    if kind=='fill-shade':
        clip=clips[i-6];points=[]
        for _,start,c1,c2,end in clip['items']:
            for j in range(33):
                t=j/32;v=start*((1-t)**3)+c1*(3*(1-t)**2*t)+c2*(3*(1-t)*t*t)+end*(t**3)
                points.append(((v.x-rect.x0)*w/rect.width,(v.y-rect.y0)*h/rect.height))
        mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon(points,fill=255)
        im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
    name=f'collie-source-component-{i}.png';im.save(a.out/name)
    s['nodes'].append(dict(id=f'collie-source-component-{i}',shape='image',asset=name,alt='Individual original gradient dot, robot/icon, surface plot or transparent shadow; internal pixels are not vector-editable',x=(rect.x0-crop.x0)*scale,y=(rect.y0-crop.y0)*scale,width=rect.width*scale,height=rect.height*scale,source_seqno=seq))
fonts={(bold,italic):fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-'+('BoldItalic' if bold and italic else 'Bold' if bold else 'Italic' if italic else 'Regular')+'.ttf') for bold in [False,True] for italic in [False,True]}
# Text remains typeable. Baseline compensation aligns the standard Arial
# substitute with source Calibri math and shape coordinates.
for n in s['nodes']:
    if n['shape']=='text':
        n['italic']='Italic' in n.get('source_font','')
        original_size=n['font_size']
        measured=fonts[n.get('bold',False),n['italic']].text_length(n['label'],fontsize=original_size)
        n['font_size']=original_size*min(1,n['width']/max(measured,.01))
        n['y']=max(0,n['y']-.15*original_size+.5*(original_size-n['font_size']))
        n['label']=n['label'].replace('ﬁ','fi').replace('ﬂ','fl')
s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
s['provenance']['text_editability']='Ordinary labels are native typeable text. Mathematical expressions are editable source glyph paths, not live equations.'
s['provenance']['font_substitutions']='Source Calibri ordinary labels use Arial with original weight/italic/color and source-baseline alignment.'
s['provenance']['image_reconstruction']='75 separate original raster components; source alpha, affine transforms and global figure crop retained. The 17 gradient dots use original cubic clip contours. Surface plot imagery is individually retained without inventing source data.'
s['provenance']['extraction_warnings_reviewed']=['Source images/shadings are reconstructed individually in source paint order. Native crop-crossing paths are white canvas or zero-opacity framing boxes. Clipping was reviewed in the source and reconstruction; the dots use exact source cubic clips.']
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(s['id'],len(s['nodes']),'objects')
