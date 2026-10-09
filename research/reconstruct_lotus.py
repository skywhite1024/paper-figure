"""Reconstruct LOTUS Figure 2 from the inspected versioned source.
Native source geometry/typeable text; individually clipped photos and shadows;
Native source formulas retain their smooth mathematical glyph outlines.
"""
import argparse,json,sys,io,copy,os,subprocess,tempfile,math
from pathlib import Path
import fitz,numpy as np,contourpy
from PIL import Image,ImageDraw
from lxml import etree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/lotus');a=p.parse_args()
c=json.loads((ROOT/'research/survey/lotus-continual-imitation-learning-for-robot-manipulation-through-unsupervised-skill-discovery-config.json').read_text());s=extract(a.pdf,c,a.out)
page=fitz.open(a.pdf)[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1];paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
assert len(blocks)==len(paints)==33
svg=ET.fromstring(page.get_svg_image(text_as_path=True).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs')
elements=[e for e in svg.iter() if (e.tag.rsplit('}',1)[-1]=='image' or (e.tag.rsplit('}',1)[-1]=='use' and e.get('data-text') is None)) and not any(p.tag.rsplit('}',1)[-1]=='defs' for p in e.iterancestors())];assert len(elements)==33
with tempfile.TemporaryDirectory(prefix='lotus-isolated-') as tmp:
    tmp=Path(tmp)
    for i,(element,b,(seq,kind,_)) in enumerate(zip(elements,blocks,paints)):
        rect=fitz.Rect(b['bbox'])&crop
        if rect.is_empty:continue
        isolated=ET.Element(svg.tag,nsmap=svg.nsmap,**dict(svg.attrib));isolated.append(copy.deepcopy(defs));isolated.set('width',str(rect.width));isolated.set('height',str(rect.height));isolated.set('viewBox',f'{rect.x0} {rect.y0} {rect.width} {rect.height}')
        chain=[];parent=element.getparent()
        while parent is not None and parent is not svg:chain.append(parent);parent=parent.getparent()
        cursor=isolated
        for ancestor in reversed(chain):
            child=ET.Element(ancestor.tag,**dict(ancestor.attrib));cursor.append(child);cursor=child
        if element.tag.rsplit('}',1)[-1]=='use':
            ref=element.get('{http://www.w3.org/1999/xlink}href')[1:];cursor.append(copy.deepcopy(svg.xpath('//*[@id=$id]',id=ref)[0]))
        else:cursor.append(copy.deepcopy(element))
        src=tmp/f'{i}.svg';src.write_bytes(ET.tostring(isolated));name=f'lotus-source-component-{i}.png'
        subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(src),str(a.out/name)],check=True,env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES','')),stdout=subprocess.DEVNULL)
        s['nodes'].append(dict(id=f'lotus-source-component-{i}',shape='image',asset=name,alt='Individual source robot photograph, database/snowflake icon, label-free gradient fill or transparent module shadow; source masks and clipping retained',x=(rect.x0-crop.x0)*scale,y=(rect.y0-crop.y0)*scale,width=rect.width*scale,height=rect.height*scale,source_seqno=seq))
# Source headings paint the same text twice (fill and hairline stroke).
# Keep one live text object, then join adjacent word spans with their real spaces.
seen_text=set();unique=[]
for n in s['nodes']:
    if n['shape']=='text':
        key=(n['label'],round(n['x'],2),round(n['y'],2),round(n['font_size'],2))
        if key in seen_text:continue
        seen_text.add(key)
    unique.append(n)
s['nodes']=unique
# Rejoin source fragments on a single baseline; formulas remain source outlines.
texts=sorted([n for n in s['nodes'] if n['shape']=='text'],key=lambda n:(round(n['y'],1),n['x']))
merged=[];removed=set()
for n in texts:
    n['bold']='Bold' in n.get('source_font','')
    prior=next((m for m in reversed(merged) if abs(m['y']-n['y'])<.3 and abs(m['font_size']-n['font_size'])<.05 and m.get('text_color')==n.get('text_color') and m.get('bold')==n.get('bold') and -.3<=n['x']-(m['x']+m['width'])<=max(.3,n['font_size']*.8)),None)
    if prior:
        prior['label']+=(' ' if n['x']-(prior['x']+prior['width'])>n['font_size']*.13 and not prior['label'].endswith(' ') and not n['label'].startswith(' ') else '')+n['label'];prior['width']=max(prior['width'],n['x']+n['width']-prior['x']);removed.add(n['id'])
    else:merged.append(n)
s['nodes']=[n for n in s['nodes'] if n['id'] not in removed]
rotated=[span for span in page.get_texttrace() if abs(span['dir'][0]-1)>1e-5 and crop.contains(fitz.Rect(span['bbox']))]
seqs={span['seqno'] for span in rotated};s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('source_seqno') in seqs)]
for span in rotated:
    r=fitz.Rect(span['bbox']);x=(r.x0-crop.x0)*scale;y=(r.y0-crop.y0)*scale;w=r.width*scale;h=r.height*scale
    s['nodes'].append(dict(id=f'lotus-rotated-label-{span["seqno"]}',shape='text',label=''.join(chr(ch[0]) for ch in span['chars']),x=x+(w-h)/2,y=y+(h-w)/2,width=h,height=w,rotation=270,font_size=span['size']*scale,font_family='Arial',bold='Bold' in span['font'],align='center',text_color='#000000',no_wrap=True,text_inset=0,source_seqno=span['seqno']))
fonts={(bold,italic):fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-'+('BoldItalic' if bold and italic else 'Bold' if bold else 'Italic' if italic else 'Regular')+'.ttf') for bold in [False,True] for italic in [False,True]}
for n in s['nodes']:
    if n['shape']!='text':continue
    n['font_family']='Arial';n['italic']=any(v in n.get('source_font','') for v in ['Italic','Oblique']);old=n['font_size'];measured=fonts[n.get('bold',False),n.get('italic',False)].text_length(n['label'],fontsize=old);n['font_size']=old*min(1,n['width']/max(measured,.01))
    if n.get('rotation'):n['x']-=.15*old
    else:n['y']=max(0,n['y']-.15*old+.5*(old-n['font_size']))
s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
# Preserve the original custom dash spacing as editable solid path segments,
# rather than accepting the Office preset's different dashes and rounded dots.
for n in list(s['nodes']):
    if n['shape']!='path' or not n.get('dash_pattern'):continue
    if n.get('fill')!='none':
        fill=copy.deepcopy(n);fill['id']+='-fill';fill['stroke']='none';fill['dash']=False;fill['dash_style']='solid';fill.pop('dash_pattern');fill.pop('dash_phase',None);s['nodes'].insert(s['nodes'].index(n),fill);n['fill']='none'
    original_commands=copy.deepcopy(n['commands']);pattern=n['dash_pattern'];subpaths=[];current=[];last=None
    for cmd in original_commands:
        if 'moveTo' in cmd:
            if current:subpaths.append(current)
            q=cmd['moveTo'];last=(q['x'],q['y']);current=[last]
        elif 'lineTo' in cmd:
            q=cmd['lineTo'];last=(q['x'],q['y']);current.append(last)
        elif 'cubicBezTo' in cmd:
            q=cmd['cubicBezTo'];p0=last;p1=(q['x1'],q['y1']);p2=(q['x2'],q['y2']);p3=(q['x'],q['y'])
            length=sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip([p0,p1,p2],[p1,p2,p3]));steps=max(4,math.ceil(length/.4))
            for step in range(1,steps+1):
                t=step/steps;u=1-t;current.append(tuple(u**3*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*p3[k] for k in (0,1)))
            last=p3
        elif 'close' in cmd:
            if current:current.append(current[0]);last=current[0]
    if current:subpaths.append(current)
    commands=[]
    for points in subpaths:
        pat=0;remaining=pattern[0];phase=n.get('dash_phase',0)%sum(pattern)
        while phase>=remaining:phase-=remaining;pat=(pat+1)%len(pattern);remaining=pattern[pat]
        remaining-=phase;active=False
        for start,end in zip(points,points[1:]):
            length=math.hypot(end[0]-start[0],end[1]-start[1]);walked=0
            if length<1e-9:continue
            while walked<length-1e-8:
                take=min(remaining,length-walked);a0=walked/length;a1=(walked+take)/length
                qa={'x':start[0]+(end[0]-start[0])*a0,'y':start[1]+(end[1]-start[1])*a0}
                qb={'x':start[0]+(end[0]-start[0])*a1,'y':start[1]+(end[1]-start[1])*a1}
                if pat%2==0:
                    if not active:commands.append({'moveTo':qa})
                    commands.append({'lineTo':qb});active=True
                else:active=False
                walked+=take;remaining-=take
                if remaining<1e-8:pat=(pat+1)%len(pattern);remaining=pattern[pat];active=False
    n['commands']=commands;n['reviewed_source_dash_pattern']=n.pop('dash_pattern');n.pop('dash_phase',None);n['dash_style']='solid';n['dash']=False;n['dash_approximation']='Source dash spacing expanded into editable native solid segments; cubic paths sampled at <=0.4 scene-pixel chord spacing'
s['provenance']['extraction_review']='Source inspected; preview and independent editor QA pending.'
s['provenance']['text_editability']='Source ordinary labels are typeable; source mathematical notation remains editable paths rather than live equations. Individual source photographs, decorative icons and source effects remain raster.'
s['provenance']['font_substitutions']='Source Helvetica-Light labels use width-fitted Arial; Computer Modern mathematical shapes retained.'
s['provenance']['extraction_warnings_reviewed']=['Every source image instance is isolated with original SVG transforms, masks and clips; no full-panel bitmap. Source custom dashed paths expanded to native editable line segments.']
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(s['id'],len(s['nodes']),'objects')
