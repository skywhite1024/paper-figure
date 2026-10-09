"""Reconstruct the inspected COLLIE Figure 1 with native ordinary labels.
Separate original images retain their affine transforms and source masks. Tiny
latent gradient dots additionally use their original Bezier clipping contours.
"""
import argparse,json,sys,math,io,copy,subprocess,os,tempfile,base64,re
from lxml import etree as ET
from pathlib import Path
import fitz,numpy as np
from PIL import Image,ImageDraw,ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/collie');a=p.parse_args()
c=json.loads((ROOT/'research/survey/collie-guiding-skill-discovery-in-semantically-coherent-latent-space-config.json').read_text());s=extract(a.pdf,c,a.out)
doc=fitz.open(a.pdf);page=doc[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1]
paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
assert len(blocks)==len(paints)==75
frame=fitz.Rect(55.439998626708984,67.06085205078125,541.424560546875,162.64097595214844)
# Isolate each source image with its complete SVG ancestry: masks, inverse
# clipping, global clip and affine transformations are all source-owned.
svg=ET.fromstring(page.get_svg_image(text_as_path=False).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs')
elements=[e for e in svg.iter() if e.tag.rsplit('}',1)[-1] in ['image','use'] and not any(a.tag.rsplit('}',1)[-1]=='defs' for a in e.iterancestors())]
assert len(elements)==len(blocks)==75
# These are literal raster drop shadows of editable words. Omit only these
# shadows so changing the native words cannot leave old lettering underneath.
text_shadow_indices={34,35,36,69,70}
image_info=page.get_image_info(xrefs=True)
with tempfile.TemporaryDirectory(prefix='collie-isolated-') as tmp:
    tmp=Path(tmp)
    for i,(element,block,(seq,kind,_)) in enumerate(zip(elements,blocks,paints)):
        if i in text_shadow_indices:continue
        rect=fitz.Rect(block['bbox'])&crop&frame
        if rect.is_empty:continue
        isolated=ET.Element(svg.tag,nsmap=svg.nsmap,**dict(svg.attrib));isolated.append(copy.deepcopy(defs))
        isolated.set('width',str(rect.width));isolated.set('height',str(rect.height));isolated.set('viewBox',f'{rect.x0} {rect.y0} {rect.width} {rect.height}')
        chain=[];parent=element.getparent()
        while parent is not None and parent is not svg:chain.append(parent);parent=parent.getparent()
        cursor=isolated
        for ancestor in reversed(chain):
            child=ET.Element(ancestor.tag,**dict(ancestor.attrib));cursor.append(child);cursor=child
        if element.tag.rsplit('}',1)[-1]=='use':
            ref=element.get('{http://www.w3.org/1999/xlink}href')[1:];resolved=svg.xpath('//*[@id=$id]',id=ref)[0]
            attrs={k:v for k,v in element.attrib.items() if not k.endswith('href')}
            if attrs:child=ET.Element('{http://www.w3.org/2000/svg}g',**attrs);cursor.append(child);cursor=child
            raster=copy.deepcopy(resolved)
        else:raster=copy.deepcopy(element)
        # PDF soft-mask /Matte means the stored colors are preblended. MuPDF's
        # SVG export retains the mask but does not unmatte these RGB values.
        # Restore straight JPEG colors before applying the original SVG mask.
        # MuPDF has already unmatted images it converts to PNG; leave those alone.
        match=next((info for info in image_info if info['xref'] and sum(abs(x-y) for x,y in zip(info['bbox'],block['bbox']))<.02),None)
        if match and block.get('mask') and Image.open(io.BytesIO(block['image'])).format=='JPEG':
            mask_key=doc.xref_get_key(match['xref'],'SMask')
            if mask_key[0]=='xref':
                matte_key=doc.xref_get_key(int(mask_key[1].split()[0]),'Matte')
                if matte_key[0]=='array':
                    matte=np.array([float(x) for x in re.findall(r'[-+]?[0-9]*[.]?[0-9]+',matte_key[1])])*255
                    source=np.asarray(Image.open(io.BytesIO(block['image'])).convert('RGB'),dtype=float)
                    alpha=np.asarray(Image.open(io.BytesIO(block['mask'])).convert('L'),dtype=float)/255
                    straight=np.clip((source-matte[None,None,:]*(1-alpha[:,:,None]))/np.maximum(alpha[:,:,None],1/255),0,255).astype('uint8')
                    buffer=io.BytesIO();Image.fromarray(straight).save(buffer,format='PNG')
                    raster.set('{http://www.w3.org/1999/xlink}href','data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode())
        cursor.append(raster)
        src=tmp/f'{i}.svg';src.write_bytes(ET.tostring(isolated));name=f'collie-source-component-{i}.png'
        env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES',os.environ.get('NODE_PATH','')))
        subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(src),str(a.out/name)],check=True,env=env,stdout=subprocess.DEVNULL)
        s['nodes'].append(dict(id=f'collie-source-component-{i}',shape='image',asset=name,alt='Isolated original icon, surface plot, gradient dot or transparent shadow with its original clipping and mask; internal pixels remain raster',x=(rect.x0-crop.x0)*scale,y=(rect.y0-crop.y0)*scale,width=rect.width*scale,height=rect.height*scale,source_seqno=seq))
# Keep the source hyphenated label as one coherent typeable span.
labels={n['id']:n for n in s['nodes']}
word=labels['pdf-text-26-0'];hyphen=labels['pdf-text-27-0']
word['label']='similar human-';word['width']=hyphen['x']+hyphen['width']-word['x']
s['nodes']=[n for n in s['nodes'] if n['id']!='pdf-text-27-0']
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
s['provenance']['image_reconstruction']='70 separate original raster components retain source SVG alpha masks, affine transforms, inverse clips and global figure crop. The 17 gradient dots keep their cubic clips. Five raster shadows of words are omitted so typeable labels leave no old lettering when edited. PDF soft-mask Matte premultiplication is reversed before mask compositing, matching source plot colors. Surface plots remain isolated original images without invented data.'
s['provenance']['extraction_warnings_reviewed']=['Source images/shadings are reconstructed individually in source paint order. Native crop-crossing paths are white canvas or zero-opacity framing boxes. Clipping was reviewed in the source and reconstruction; the dots use exact source cubic clips. Raster word shadows are intentionally omitted.']
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(s['id'],len(s['nodes']),'objects')
