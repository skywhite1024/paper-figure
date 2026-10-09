"""Reconstruct SymSkill Figure 2 from the inspected versioned source.
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
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/symskill');a=p.parse_args()
c=json.loads((ROOT/'research/survey/symskill-symbol-and-skill-co-invention-for-data-efficient-and-reactive-long-horizon-manipulation-config.json').read_text());s=extract(a.pdf,c,a.out)
page=fitz.open(a.pdf)[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
# The source contains empty glyph paints for spaces. PyMuPDF drawings omit
# those paints while bboxlog retains them; map to true paint order before
# interleaving separately isolated source images.
paint_log=page.get_bboxlog()
nonempty_paints=[i for i,(_,b) in enumerate(paint_log) if b[0]<b[2] and b[1]<b[3]]
for n in s['nodes']:
    if n['shape']=='path' and n.get('source_seqno',100000)<100000:
        n['source_seqno']=nonempty_paints[n['source_seqno']]
# Readable source labels were converted to outlines by its author and have an
# invisible accessibility-text layer. Replace only geometrically matched glyphs.
restored=[];removed_glyphs=set()
for index,span in enumerate(page.get_texttrace()):
    r=fitz.Rect(span['bbox']);label=''.join(chr(ch[0]) for ch in span['chars'])
    if span.get('type')!=3 or not label.strip() or not crop.contains(r):continue
    boxes=[fitz.Rect(ch[3])+(-.35,-.35,.35,.35) for ch in span['chars'] if not chr(ch[0]).isspace()]
    matches=[]
    for n in s['nodes']:
        if n['shape']!='path' or n.get('stroke')!='none' or n.get('fill')=='none':continue
        nr=fitz.Rect(n['x']/scale+crop.x0,n['y']/scale+crop.y0,(n['x']+n['width'])/scale+crop.x0,(n['y']+n['height'])/scale+crop.y0)
        if nr.height<span['size']*1.2 and (r+(-.6,-.6,.6,.6)).contains(nr):matches.append(n)
    assert matches, 'No visible glyphs matched '+label
    from collections import Counter
    fill=Counter(n['fill'] for n in matches).most_common(1)[0][0]
    matches=[n for n in matches if n['fill']==fill]
    removed_glyphs.update(n['id'] for n in matches)
    import re
    runs=list(re.finditer(r'\S(?:.*?\S)?(?= {2,}|$)',label)) if '  ' in label else [re.match(r'.*',label)]
    for ri,run in enumerate(runs):
        chars=span['chars'][run.start():run.end()];rr=fitz.Rect(chars[0][3])
        for ch in chars[1:]:rr|=fitz.Rect(ch[3])
        restored.append(dict(id=f'symskill-live-label-{index}-{ri}',shape='text',label=run.group(),x=(rr.x0-crop.x0)*scale,y=(rr.y0-crop.y0)*scale,width=rr.width*scale,height=rr.height*scale,font_size=span['size']*scale,font_family='Arial',source_font='Helvetica-Bold' if label=='Replanning' else 'Helvetica',bold=label=='Replanning',align='left',text_color=fill,no_wrap=True,text_inset=0,source_seqno=max(n['source_seqno'] for n in matches)))
s['nodes']=[n for n in s['nodes'] if n['id'] not in removed_glyphs]+restored
print('Restored',len(restored),'ordinary labels from',len(removed_glyphs),'matched outlines')
blocks=page.get_image_info(xrefs=True)
raw_blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1];paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
assert len(blocks)==len(paints)==10
svg=ET.fromstring(page.get_svg_image(text_as_path=True).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs')
elements=[e for e in svg.iter() if (e.tag.rsplit('}',1)[-1]=='image' or (e.tag.rsplit('}',1)[-1]=='use' and e.get('data-text') is None)) and not any(p.tag.rsplit('}',1)[-1]=='defs' for p in e.iterancestors())];assert len(elements)==10
with tempfile.TemporaryDirectory(prefix='symskill-isolated-') as tmp:
    tmp=Path(tmp)
    for i,(element,b,(seq,kind,_)) in enumerate(zip(elements,blocks,paints)):
        rect=fitz.Rect(b['bbox'])&crop
        if rect.is_empty:continue
        if i in {4,6,8}:
            raw=next(q for q in raw_blocks if sum(abs(x-y) for x,y in zip(q['bbox'],b['bbox']))<.02)
            pix=fitz.Pixmap(raw['image']);pix=fitz.Pixmap(pix,0) if pix.alpha else pix
            if raw.get('mask'):pix=fitz.Pixmap(pix,fitz.Pixmap(raw['mask']))
            bitmap=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA');arr=np.asarray(bitmap);alpha=(1-arr[:,:,:3].max(2).astype(float)/255)*arr[:,:,3]/255
            dx=rect.width*scale/bitmap.width;dy=rect.height*scale/bitmap.height;ox=(rect.x0-crop.x0)*scale;oy=(rect.y0-crop.y0)*scale
            points,offsets=contourpy.contour_generator(z=np.pad(alpha,1),fill_type='OuterOffset').filled(.5,1.1)
            for j,(pts,off) in enumerate(zip(points,offsets)):
                pts=pts-.5;x0=float(pts[:,0].min());x1=float(pts[:,0].max());y0=float(pts[:,1].min());y1=float(pts[:,1].max());commands=[]
                for start,end in zip(off[:-1],off[1:]):
                    for k,(x,y) in enumerate(pts[int(start):int(end)]):commands.append({('moveTo' if k==0 else 'lineTo'):{'x':float((x-x0)*dx),'y':float((y-y0)*dy)}})
                    commands.append({'close':{}})
                s['nodes'].append(dict(id=f'symskill-math-{i}-glyph-{j}',shape='path',x=ox+x0*dx,y=oy+y0*dy,width=max(.01,(x1-x0)*dx),height=max(.01,(y1-y0)*dy),commands=commands,fill='#000000',stroke='none',stroke_width=0,source_seqno=seq))
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
        src=tmp/f'{i}.svg';src.write_bytes(ET.tostring(isolated));name=f'symskill-source-component-{i}.png'
        subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(src),str(a.out/name)],check=True,env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES','')),stdout=subprocess.DEVNULL)
        # Trim invisible source image extents after exact SVG clipping.
        bitmap=Image.open(a.out/name).convert('RGBA');alpha_bbox=bitmap.getchannel('A').getbbox()
        if alpha_bbox is None:continue
        x0,y0,x1,y1=alpha_bbox;px=rect.width/bitmap.width;py=rect.height/bitmap.height;bitmap.crop(alpha_bbox).save(a.out/name)
        rr=fitz.Rect(rect.x0+x0*px,rect.y0+y0*py,rect.x0+x1*px,rect.y0+y1*py)
        s['nodes'].append(dict(id=f'symskill-source-component-{i}',shape='image',asset=name,alt='Individual original camera/brand icon, photograph, segmentation chart or 3D policy plot; source SVG masks/clipping retained, internal annotations remain raster',x=(rr.x0-crop.x0)*scale,y=(rr.y0-crop.y0)*scale,width=rr.width*scale,height=rr.height*scale,source_seqno=seq))

# Rejoin source fragments on a single baseline; formulas remain source outlines.
texts=sorted([n for n in s['nodes'] if n['shape']=='text'],key=lambda n:(round(n['y'],1),n['x']))
merged=[];removed=set()
for n in texts:
    n['bold']='Bold' in n.get('source_font','')
    prior=next((m for m in reversed(merged) if abs(m['y']-n['y'])<.3 and abs(m['font_size']-n['font_size'])<.05 and m.get('text_color')==n.get('text_color') and m.get('bold')==n.get('bold') and -.3<=n['x']-(m['x']+m['width'])<=max(.3,n['font_size']*.08)),None)
    if prior:
        prior['label']+=n['label'];prior['width']=max(prior['width'],n['x']+n['width']-prior['x']);removed.add(n['id'])
    else:merged.append(n)
s['nodes']=[n for n in s['nodes'] if n['id'] not in removed]
rotated=[span for span in page.get_texttrace() if abs(span['dir'][0]-1)>1e-5 and crop.contains(fitz.Rect(span['bbox']))]
seqs={span['seqno'] for span in rotated};s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('source_seqno') in seqs)]
for span in rotated:
    r=fitz.Rect(span['bbox']);x=(r.x0-crop.x0)*scale;y=(r.y0-crop.y0)*scale;w=r.width*scale;h=r.height*scale
    s['nodes'].append(dict(id=f'symskill-rotated-label-{span["seqno"]}',shape='text',label=''.join(chr(ch[0]) for ch in span['chars']),x=x+(w-h)/2,y=y+(h-w)/2,width=h,height=w,rotation=270,font_size=span['size']*scale,font_family='Arial',bold='Bold' in span['font'],align='center',text_color='#000000',no_wrap=True,text_inset=0,source_seqno=span['seqno']))
fonts={bold:fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-'+('Bold' if bold else 'Regular')+'.ttf') for bold in [False,True]}
for n in s['nodes']:
    if n['shape']!='text':continue
    n['font_family']='Arial';n['italic']='Oblique' in n.get('source_font','');old=n['font_size'];measured=fonts[n.get('bold',False)].text_length(n['label'],fontsize=old);n['font_size']=old*min(1,n['width']/max(measured,.01))
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
# Two photograph-internal object-type callouts are rebuilt as native bubbles
# and text at their inspected source positions; the photo and RGB axes remain.
photo=next(n for n in s['nodes'] if n['id']=='symskill-source-component-2')
for i,(label,bx,by,bw,bh) in enumerate([('cabinet type',32,69.5,66.5,25),('lid type',173,77,66.5,25)]):
    r=11.5;k=.5522847498;commands=[{'moveTo':{'x':r,'y':0}},{'lineTo':{'x':bw-r,'y':0}},{'cubicBezTo':{'x1':bw-r+k*r,'y1':0,'x2':bw,'y2':r-k*r,'x':bw,'y':r}},{'lineTo':{'x':bw,'y':bh-r}},{'cubicBezTo':{'x1':bw,'y1':bh-r+k*r,'x2':bw-r+k*r,'y2':bh,'x':bw-r,'y':bh}},{'lineTo':{'x':r,'y':bh}},{'cubicBezTo':{'x1':r-k*r,'y1':bh,'x2':0,'y2':bh-r+k*r,'x':0,'y':bh-r}},{'lineTo':{'x':0,'y':r}},{'cubicBezTo':{'x1':0,'y1':r-k*r,'x2':r-k*r,'y2':0,'x':r,'y':0}},{'close':{}}]
    s['nodes'].append(dict(id=f'symskill-object-type-bubble-{i}',shape='path',x=photo['x']+bx,y=photo['y']+by,width=bw,height=bh,commands=commands,fill='#CDE1FC',stroke='#222222',stroke_width=.8,source_seqno=517.1))
    s['nodes'].append(dict(id=f'symskill-object-type-label-{i}',shape='text',label=label,x=photo['x']+bx+1,y=photo['y']+by+6,width=bw-2,height=12,font_size=9.5,font_family='Arial',text_color='#000000',align='center',text_inset=0,no_wrap=True,source_seqno=517.2))
s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
s['provenance']['extraction_review']='Source inspected; generated preview and independent editor QA pending.'
s['provenance']['text_editability']='Ordinary source labels, including cabinet type and lid type callouts, are typeable text. Three raster math labels are point-editable native contours, not live equations. Source plot and remaining photo-internal annotations remain raster.'
s['provenance']['font_substitutions']='Source Helvetica/accessibility labels use width-fitted Arial; visible Replanning heading restored with its source bold appearance.'
s['provenance']['dash_fidelity']='Source custom dashed boundaries expanded into native solid segments with <=0.4 scene-pixel chord sampling.'
s['provenance']['extraction_warnings_reviewed']=['Ten source image instances reviewed. Three formula rasters traced to native glyph paths; seven images isolated with exact source transforms, masks and clips, then transparent extents trimmed. The segmentation chart is absent from get_text image blocks but recovered from source image_info and source SVG. Two plots retain source internal data pixels, without invented native plot data.']
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(s['id'],len(s['nodes']),'objects')
