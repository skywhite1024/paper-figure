"""Reproduce FoG Figure 1; live prose/code, source math contours, isolated icons."""
import argparse,json,sys,io,copy,os,subprocess,tempfile,math,re
from pathlib import Path
import fitz,numpy as np,contourpy
from PIL import Image
from lxml import etree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import paper_figure.pdf_extract as extractor
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/fog');a=p.parse_args()
c=json.loads((ROOT/'research/survey/guiding-skill-discovery-with-foundation-models-config.json').read_text())
# The custom embedded font exposes two malformed UTF-16 emoji placeholders.
# The visible globe has its own original image; remove only those placeholders
# before XML validation. This changes no shared extractor source files.
original_validate=extractor.validate
def valid_source_text(scene,base):
    scene['nodes']=[n for n in scene['nodes'] if not any(0xD800<=ord(ch)<=0xDFFF for ch in n.get('label',''))]
    return validate(scene,base)
extractor.validate=valid_source_text
try:s=extractor.extract(a.pdf,c,a.out)
finally:extractor.validate=original_validate
page=fitz.open(a.pdf)[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1]
paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
assert len(blocks)==len(paints)==26
svg=ET.fromstring(page.get_svg_image(text_as_path=True).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs')
elements=[e for e in svg.iter() if (e.tag.rsplit('}',1)[-1]=='image' or (e.tag.rsplit('}',1)[-1]=='use' and e.get('data-text') is None)) and not any(p.tag.rsplit('}',1)[-1]=='defs' for p in e.iterancestors())]
assert len(elements)==26
formula_indices={12,13,16,22,23,24}
with tempfile.TemporaryDirectory(prefix='fog-isolated-') as tmp:
    tmp=Path(tmp)
    for i,(element,b,(seq,kind,_)) in enumerate(zip(elements,blocks,paints)):
        rect=fitz.Rect(b['bbox'])
        if not crop.contains(rect):continue
        if i in formula_indices:
            raw=Image.open(io.BytesIO(b['image'])).convert('RGBA')
            rgb=np.asarray(raw)[:,:,:3].astype(float)
            alpha=(1-rgb.mean(2)/255)*np.asarray(raw.getchannel('A'),dtype=float)/255
            if b.get('mask'):alpha*=np.asarray(Image.open(io.BytesIO(b['mask'])).convert('L'),dtype=float)/255
            dx=rect.width*scale/raw.width;dy=rect.height*scale/raw.height;ox=(rect.x0-crop.x0)*scale;oy=(rect.y0-crop.y0)*scale
            points,offsets=contourpy.contour_generator(z=np.pad(alpha,1),fill_type='OuterOffset').filled(.5,1.1)
            for j,(pts,off) in enumerate(zip(points,offsets)):
                pts=pts-.5;x0=float(pts[:,0].min());x1=float(pts[:,0].max());y0=float(pts[:,1].min());y1=float(pts[:,1].max());commands=[]
                for start,end in zip(off[:-1],off[1:]):
                    for k,(x,y) in enumerate(pts[int(start):int(end)]):commands.append({('moveTo' if k==0 else 'lineTo'):{'x':float((x-x0)*dx),'y':float((y-y0)*dy)}})
                    commands.append({'close':{}})
                s['nodes'].append(dict(id=f'fog-math-{i}-glyph-{j}',shape='path',x=ox+x0*dx,y=oy+y0*dy,width=(x1-x0)*dx,height=(y1-y0)*dy,commands=commands,fill='#000000',stroke='none',stroke_width=0,source_seqno=seq))
            continue
        isolated=ET.Element(svg.tag,nsmap=svg.nsmap,**dict(svg.attrib));isolated.append(copy.deepcopy(defs));isolated.set('width',str(rect.width));isolated.set('height',str(rect.height));isolated.set('viewBox',f'{rect.x0} {rect.y0} {rect.width} {rect.height}')
        chain=[];parent=element.getparent()
        while parent is not None and parent is not svg:chain.append(parent);parent=parent.getparent()
        cursor=isolated
        for ancestor in reversed(chain):
            child=ET.Element(ancestor.tag,**dict(ancestor.attrib));cursor.append(child);cursor=child
        if element.tag.rsplit('}',1)[-1]=='use':
            ref=element.get('{http://www.w3.org/1999/xlink}href')[1:];cursor.append(copy.deepcopy(svg.xpath('//*[@id=$id]',id=ref)[0]))
        else:cursor.append(copy.deepcopy(element))
        src=tmp/f'{i}.svg';src.write_bytes(ET.tostring(isolated));name=f'fog-source-component-{i}.png'
        subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(src),str(a.out/name)],check=True,env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES','')),stdout=subprocess.DEVNULL)
        s['nodes'].append(dict(id=f'fog-source-component-{i}',shape='image',asset=name,alt='Individual original model/environment icon or transparent shadow with source masks and clipping; internal pixels remain raster',x=(rect.x0-crop.x0)*scale,y=(rect.y0-crop.y0)*scale,width=rect.width*scale,height=rect.height*scale,source_seqno=seq))
# Source Office-style stroking is in local units, unlike get_drawings path
# coordinates. Recover the actual stroke scale from the source SVG transform.
scales=[]
for e in svg.iter():
    if float(e.get('stroke-width','0'))>100:
        values=[float(v) for v in re.findall(r'[-+]?(?:[0-9]*[.])?[0-9]+(?:[eE][-+]?[0-9]+)?',e.get('transform',''))]
        assert len(values)==6 and abs(values[1])+abs(values[2])<1e-8
        scales.append(math.sqrt(abs(values[0]*values[3])))
assert scales and max(scales)-min(scales)<1e-9
stroke_scale=scales[0]
for n in s['nodes']:
    if n['shape']=='path' and n.get('stroke_width',0)>100:
        n['stroke_width']*=stroke_scale
        if n.get('dash_pattern'):n['dash_pattern']=[v*stroke_scale for v in n['dash_pattern']];n['dash_phase']*=stroke_scale
s['provenance']['stroke_scale_repair']=f'Source SVG verifies {stroke_scale:.12g} local-to-page stroke scale; native line widths and dash intervals corrected from raw Office units.'
# Recover the two rotated labels as typeable single text boxes.
rotated=[span for span in page.get_texttrace() if span['dir']!=(1.,0.) and crop.contains(fitz.Rect(span['bbox']))]
rotated_seq={span['seqno'] for span in rotated}
s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('source_seqno') in rotated_seq)]
for span in rotated:
    r=fitz.Rect(span['bbox']);x=(r.x0-crop.x0)*scale;y=(r.y0-crop.y0)*scale;w=r.width*scale;h=r.height*scale
    label=''.join(chr(ch[0]) for ch in span['chars']);s['nodes'].append(dict(id=f'fog-rotated-label-{span["seqno"]}',shape='text',label=label,x=x+(w-h)/2,y=y+(h-w)/2,width=h,height=w,rotation=270,font_size=span['size']*scale,font_family='Arial',align='center',text_color='#000000',no_wrap=True,text_inset=0,source_seqno=span['seqno']))
fonts={bold:fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-'+('Bold' if bold else 'Regular')+'.ttf') for bold in [False,True]}
for n in s['nodes']:
    if n['shape']!='text':continue
    if n['label'].strip().startswith(('def score_fn','y_coord','...')):n['font_family']='Courier New';n['bold']=True
    elif n['label']=='CLIP':n['bold']=True
    old=n['font_size']
    if n['font_family']!='Courier New':
        measured=fonts[n.get('bold',False)].text_length(n['label'],fontsize=old);n['font_size']=old*min(1,n['width']/max(measured,.01))
    if not n.get('rotation'):n['y']=max(0,n['y']-.15*old+.5*(old-n['font_size']))
    else:n['x']-=.15*old
s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
s['provenance']['text_editability']='Ordinary labels, the state/pixel vertical labels and the complete score function code are native typeable text. Six source formula images are individual editable native glyph contours, not live equations.'
s['provenance']['font_substitutions']='Custom unnamed source fonts use width-fitted Arial; code uses bold Courier New. Original mathematical formula bitmap contours retained.'
s['provenance']['extraction_warnings_reviewed']=['All in-crop raster instances handled separately. Formula source bitmaps traced; model/environment icons isolated with source SVG clips/masks. Malformed surrogate emoji placeholders removed because the visible original globe image is retained. Rotated labels restored as native rotated text boxes.']
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(s['id'],len(s['nodes']),'objects')
