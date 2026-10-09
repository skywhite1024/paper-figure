"""Reconstruct Conquer Figure 1 from the inspected versioned source.
Native source geometry/typeable text; individually clipped photos and shadows;
source-raster SAG panel rebuilt as native shapes, labels and math contours.
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
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True,type=Path);p.add_argument('--out',type=Path,default=ROOT/'data/diagrams/conquer');a=p.parse_args()
c=json.loads((ROOT/'research/survey/continual-quadruped-robots-coordination-via-semantic-skill-discovery-config.json').read_text());s=extract(a.pdf,c,a.out)
page=fitz.open(a.pdf)[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
blocks=[b for b in page.get_text('dict')['blocks'] if b['type']==1];paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
assert len(blocks)==len(paints)==40
svg=ET.fromstring(page.get_svg_image(text_as_path=True).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs')
elements=[e for e in svg.iter() if (e.tag.rsplit('}',1)[-1]=='image' or (e.tag.rsplit('}',1)[-1]=='use' and e.get('data-text') is None)) and not any(p.tag.rsplit('}',1)[-1]=='defs' for p in e.iterancestors())];assert len(elements)==40
with tempfile.TemporaryDirectory(prefix='conquer-isolated-') as tmp:
    tmp=Path(tmp)
    for i,(element,b,(seq,kind,_)) in enumerate(zip(elements,blocks,paints)):
        # 7 is the literal raster shadow of the typeable instruction letter M;
        # 38 is the complete SAG bitmap panel, rebuilt below instead.
        if i in {7,38}:continue
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
        src=tmp/f'{i}.svg';src.write_bytes(ET.tostring(isolated));name=f'conquer-source-component-{i}.png'
        subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(src),str(a.out/name)],check=True,env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES','')),stdout=subprocess.DEVNULL)
        # These original gradient arrows sit on a uniform #F2F2F2 surface.
        # Precompose only nonzero-alpha arrow pixels to avoid LibreOffice's
        # grainy semi-transparent mask rendering; transparent exterior stays empty.
        if i in {13,14,15,18,26,27,28,29,39}:
            arr=np.asarray(Image.open(a.out/name).convert('RGBA')).copy();alpha=arr[:,:,3:4].astype(float)/255
            arr[:,:,:3]=np.rint(arr[:,:,:3]*alpha+242*(1-alpha)).astype('uint8');arr[:,:,3]=np.where(arr[:,:,3]>0,255,0).astype('uint8');Image.fromarray(arr).save(a.out/name)
        s['nodes'].append(dict(id=f'conquer-source-component-{i}',shape='image',asset=name,alt='Isolated original photograph, VLM icon, gradient arrow or transparent shadow with original source clipping; internal pixels remain raster',x=(rect.x0-crop.x0)*scale,y=(rect.y0-crop.y0)*scale,width=rect.width*scale,height=rect.height*scale,source_seqno=seq))
# Rejoin contiguous source text fragments so ordinary headings/descriptors can
# be edited as whole words. No mathematical outline is duplicated underneath.
for n in s['nodes']:
    if n['shape']=='text':n['italic']='Ital' in n.get('source_font','')
rotated=[span for span in page.get_texttrace() if span['dir']!=(1.,0.) and 'CambriaMath' not in span['font'] and crop.contains(fitz.Rect(span['bbox']))]
rotated_seq={span['seqno'] for span in rotated};s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('source_seqno') in rotated_seq)]
texts=sorted([n for n in s['nodes'] if n['shape']=='text'],key=lambda n:(round(n['y'],1),n['x']))
merged=[];removed=set()
for n in texts:
    prior=next((m for m in reversed(merged) if abs(m['y']-n['y'])<.3 and abs(m['font_size']-n['font_size'])<.05 and m.get('text_color')==n.get('text_color') and m.get('bold')==n.get('bold') and m.get('italic')==n.get('italic') and -.3<=n['x']-(m['x']+m['width'])<=max(.3,n['font_size']*.08)),None)
    if prior:
        prior['label']+=n['label'];prior['width']=max(prior['width'],n['x']+n['width']-prior['x']);removed.add(n['id'])
    else:merged.append(n)
s['nodes']=[n for n in s['nodes'] if n['id'] not in removed]
for n in s['nodes']:
    if n['shape']=='text':n['y']=max(0,n['y']-.15*n['font_size']);n['label']=n['label'].replace('ﬁ','fi').replace('ﬂ','fl')
for span in rotated:
    r=fitz.Rect(span['bbox']);x=(r.x0-crop.x0)*scale;y=(r.y0-crop.y0)*scale;w=r.width*scale;h=r.height*scale
    s['nodes'].append(dict(id=f'conquer-rotated-label-{span["seqno"]}',shape='text',label=''.join(chr(ch[0]) for ch in span['chars']),x=x+(w-h)/2-.15*span['size']*scale,y=y+(h-w)/2,width=h,height=w,rotation=270,font_size=span['size']*scale,font_family='Times New Roman',align='center',text_color='#000000',no_wrap=True,text_inset=0,source_seqno=span['seqno']))
# Rotated source ellipse widths in get_drawings use the first matrix component.
# Recover the actual uniform scale from the complete source SVG matrix norm.
for source_color, seqno in [('#4472c4',87),('#ed7d31',88),('#ffc000',89)]:
    matches=[e for e in svg.iter() if e.get('stroke','').lower()==source_color and e.get('stroke-dasharray')]
    assert len(matches)==1,(source_color,len(matches))
    e=matches[0]; matrix=[float(v) for v in e.get('transform')[7:-1].replace(',',' ').split()]
    factor=math.hypot(matrix[0],matrix[1])*scale
    n=next(n for n in s['nodes'] if n['id']==f'pdf-path-{seqno}')
    n['stroke_width']=float(e.get('stroke-width'))*factor
    n['dash_pattern']=[float(v)*factor for v in e.get('stroke-dasharray').split(',')]
    n['source_svg_stroke_scale_review']='Full SVG transform vector norm, correcting rotated MuPDF width'
s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
# SAG source bitmap, inspected at its native 1244x679 resolution.
b=blocks[38];pix=fitz.Pixmap(b['image'])
if pix.alpha:pix=fitz.Pixmap(pix,0)
if b.get('mask'):pix=fitz.Pixmap(pix,fitz.Pixmap(b['mask']))
im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA');assert im.size==(1244,679)
box=fitz.Rect(b['bbox']);dx=box.width*scale/im.width;dy=box.height*scale/im.height;ox=(box.x0-crop.x0)*scale;oy=(box.y0-crop.y0)*scale
seq=paints[38][0]
def base(name,x,y,w,h):return dict(id='sag-'+name,x=ox+x*dx,y=oy+y*dy,width=max(.01,w*dx),height=max(.01,h*dy),source_seqno=seq)
def rect(name,x,y,w,h,fill,stroke='#000000',weight=3,rounded=False,dash=False):
    if not rounded:
        s['nodes'].append(dict(**base(name,x,y,w,h),shape='rect',fill=fill,stroke=stroke,stroke_width=weight*dx,dash=dash));return
    # Explicit source-measured corner radii avoid the PPTX default rounding.
    r=(8 if name.startswith('feature-') else 14 if name.endswith('-box') else 60 if name in ('lora-module','lochead-module','library-region') else 29)
    r=min(r,w/2,h/2);k=.55228475
    cmds=[{'moveTo':{'x':r*dx,'y':0}},{'lineTo':{'x':(w-r)*dx,'y':0}},
          {'cubicBezTo':{'x1':(w-r+k*r)*dx,'y1':0,'x2':w*dx,'y2':(r-k*r)*dy,'x':w*dx,'y':r*dy}},
          {'lineTo':{'x':w*dx,'y':(h-r)*dy}},
          {'cubicBezTo':{'x1':w*dx,'y1':(h-r+k*r)*dy,'x2':(w-r+k*r)*dx,'y2':h*dy,'x':(w-r)*dx,'y':h*dy}},
          {'lineTo':{'x':r*dx,'y':h*dy}},
          {'cubicBezTo':{'x1':(r-k*r)*dx,'y1':h*dy,'x2':0,'y2':(h-r+k*r)*dy,'x':0,'y':(h-r)*dy}},
          {'lineTo':{'x':0,'y':r*dy}},
          {'cubicBezTo':{'x1':0,'y1':(r-k*r)*dy,'x2':(r-k*r)*dx,'y2':0,'x':r*dx,'y':0}},{'close':{}}]
    s['nodes'].append(dict(**base(name,x,y,w,h),shape='path',commands=cmds,fill=fill,stroke=stroke,stroke_width=weight*dx,dash=dash))
def polygon(name,points,fill,stroke='#000000',weight=3):
    x=min(q[0] for q in points);y=min(q[1] for q in points);w=max(q[0] for q in points)-x;h=max(q[1] for q in points)-y
    cmds=[{('moveTo' if i==0 else 'lineTo'):{'x':(qx-x)*dx,'y':(qy-y)*dy}} for i,(qx,qy) in enumerate(points)]+[{'close':{}}]
    s['nodes'].append(dict(**base(name,x,y,w,h),shape='path',commands=cmds,fill=fill,stroke=stroke,stroke_width=weight*dx))
def arrow(name,points,width=5):
    x=min(q[0] for q in points);y=min(q[1] for q in points);w=max(q[0] for q in points)-x;h=max(q[1] for q in points)-y
    cmds=[{('moveTo' if i==0 else 'lineTo'):{'x':(qx-x)*dx,'y':(qy-y)*dy}} for i,(qx,qy) in enumerate(points)]
    s['nodes'].append(dict(**base(name,x,y,w,h),shape='path',commands=cmds,fill='none',stroke='#000000',stroke_width=width*dx))
    px,py=points[-2];ex,ey=points[-1];ux,uy=ex-px,ey-py;length=math.hypot(ux,uy);ux/=length;uy/=length
    polygon(name+'-head',[(ex,ey),(ex-ux*18-uy*9,ey-uy*18+ux*9),(ex-ux*18+uy*9,ey-uy*18-ux*9)],'#000000','none',0)
# Source shape fills sampled from unobstructed interiors of the original bitmap.
rect('library-region',5,41,448,622,'#F2F2F2','#BFBFBF',5,True,True)
rect('lora-module',31,72,391,175,'#DAE3F3','#8FAADC',4,True)
rect('lochead-module',39,386,389,173,'#D9D9D9','#A5A5A5',4,True)
# Keep the two original purple halos as masked source glow rings. No border,
# mathematical text or rectangular panel background survives in these insets.
for k,(roi,inside,bg) in enumerate([((165,136,283,245),(181,153,268,226),(218,227,243)),((171,450,286,553),(187,467,274,540),(217,217,217))]):
    asset=im.crop(roi);arr=np.asarray(asset).copy();rgb=arr[:,:,:3].astype(int);mask=(np.max(np.abs(rgb-np.array(bg)),axis=2)>3)&(rgb.max(2)>100)
    xx0,yy0,xx1,yy1=inside;mask[max(0,yy0-roi[1]):yy1-roi[1],max(0,xx0-roi[0]):xx1-roi[0]]=False;arr[:,:,3]=arr[:,:,3]*mask
    name=f'conquer-sag-glow-{k}.png';Image.fromarray(arr).save(a.out/name);s['nodes'].append(dict(**base('glow-'+str(k),roi[0],roi[1],roi[2]-roi[0],roi[3]-roi[1]),shape='image',asset=name,alt='Isolated original purple selection glow; central old glyph and border removed'))
for name,x,y,w,h,color in [('phi1',59,156,82,67,'#8FAADC'),('phistar',184,157,81,66,'#B493C7'),('phiN',311,157,81,66,'#8FAADC'),('omega1',64,470,81,68,'#FBE5D6'),('omegastar',189,470,82,67,'#B493C7'),('omegaN',315,469,83,68,'#FBE5D6')]:rect(name+'-box',x,y,w,h,color,'#000000',3,True)
for k,(x,color) in enumerate([(496,'#8FAADC'),(736,'#FFD966'),(975,'#F4B183')]):
    for j in range(3):rect(f'feature-{k}-{j}',x+j*59,73,42,43,'#F2F2F2',color,4,True)
for k,(x,color,stroke) in enumerate([(489,'#DAE3F3','#8FAADC'),(727,'#FFF2CC','#FFD966'),(966,'#FBE5D6','#F4B183')]):polygon('linear-'+str(k),[(x,120),(x+176,120),(x+155,205),(x+21,205)],color,stroke,4)
rect('cross-attention',511,252,612,86,'#D0CECE','#7F7F7F',3,True)
rect('fusion',638,384,370,72,'#FBE5D6','#F8CBAD',4,True)
rect('fused-feature',670,486,290,65,'#EDEDED','#D9D9D9',4)
rect('action-decoder',519,588,612,84,'#D0CECE','#7F7F7F',3,True)
for k,x in enumerate([575,815,1054]):arrow('feature-down-'+str(k),[(x,205),(x,249)])
arrow('lora-to-attention',[(224,225),(224,294),(508,294)])
arrow('attention-to-fusion',[(816,338),(816,381)])
arrow('fusion-to-feature',[(816,456),(816,484)])
arrow('feature-to-decoder',[(816,552),(816,585)])
arrow('head-to-decoder',[(230,538),(230,630),(516,630)])
# Isolate only the colored training/frozen-state icons from the source panel.
for name,roi,kind in [('fire-top',(311,76,368,142),'red'),('fire-bottom',(312,390,368,455),'red'),('snow-top',(1034,266,1100,326),'blue'),('snow-bottom',(1034,598,1101,660),'blue')]:
    asset=im.crop(roi);arr=np.asarray(asset).copy();rgb=arr[:,:,:3].astype(float)
    strength=np.clip((rgb[:,:,0]-np.maximum(rgb[:,:,1],rgb[:,:,2]))/120,0,1) if kind=='red' else np.clip((rgb[:,:,2]-rgb[:,:,0])/140,0,1)
    arr[:,:,3]=(arr[:,:,3]*strength).astype('uint8');file=f'conquer-sag-{name}.png';Image.fromarray(arr).save(a.out/file)
    s['nodes'].append(dict(**base(name,roi[0],roi[1],roi[2]-roi[0],roi[3]-roi[1]),shape='image',asset=file,alt='Isolated original flame or snowflake icon; source colored pixels retained'))
fonts={False:fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'),True:fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf')}
def ordinary(name,text,roi,bold=False):
    raw=np.asarray(im.crop(roi));rgb=raw[:,:,:3];mask=(rgb.max(2)<100)&(raw[:,:,3]>128);yy,xx=np.where(mask)
    assert len(xx),name
    x=roi[0]+int(xx.min());y=roi[1]+int(yy.min());w=int(xx.max()-xx.min()+1);h=int(yy.max()-yy.min()+1)
    font=w/max(fonts[bold].text_length(text,fontsize=1),.01)
    s['nodes'].append(dict(**base(name,x,y-font*.15,w+1,font),shape='text',label=text,font_family='Times New Roman',font_size=font*dx,bold=bold,align='left',text_color='#000000',text_inset=0,no_wrap=True))
for args in [('lora-label','LoRA',(70,84,214,140)),('lochead-label','LocHead',(70,399,283,450)),('self-features','Self Features',(467,12,681,61)),('ally-features','Ally Features',(700,12,942,61)),('goal-features','Goal Features',(945,12,1194,61)),('linear-label-0','Linear',(507,135,653,193)),('linear-label-1','Linear',(750,135,895,193)),('linear-label-2','Linear',(988,135,1130,193)),('cross-attention-label','Cross-Attention layer',(626,266,1022,324)),('fusion-label','Fusion MLP',(714,397,948,451)),('fused-label','Fused feature',(684,494,905,546)),('decoder-label','Action Decoder',(621,604,883,663)),('dots-0','...',(146,184,179,214)),('dots-1','...',(271,184,307,214)),('dots-2','...',(152,493,185,524)),('dots-3','...',(277,493,309,524))]:ordinary(*args)
# Mathematical labels preserve their actual original raster glyph silhouettes
# as individual native contours, without retaining the source mini-panel.
for name,roi in [('phi1',(76,165,131,218)),('phistar',(201,165,254,218)),('phiN',(328,165,385,218)),('omega1',(77,482,134,530)),('omegastar',(205,482,259,530)),('omegaN',(331,482,391,530)),('feature-hi',(909,495,951,544)),('policy',(881,604,1025,663))]:
    raw=np.asarray(im.crop(roi));alpha=(1-raw[:,:,:3].max(2).astype(float)/255)*raw[:,:,3]/255
    points,offsets=contourpy.contour_generator(z=np.pad(alpha,1),fill_type='OuterOffset').filled(.5,1.1)
    for j,(pts,off) in enumerate(zip(points,offsets)):
        pts=pts-.5;x0=float(pts[:,0].min());x1=float(pts[:,0].max());y0=float(pts[:,1].min());y1=float(pts[:,1].max());commands=[]
        for start,end in zip(off[:-1],off[1:]):
            for k,(x,y) in enumerate(pts[int(start):int(end)]):commands.append({('moveTo' if k==0 else 'lineTo'):{'x':float((x-x0)*dx),'y':float((y-y0)*dy)}})
            commands.append({'close':{}})
        s['nodes'].append(dict(**base(name+'-glyph-'+str(j),roi[0]+x0,roi[1]+y0,x1-x0,y1-y0),shape='path',commands=commands,fill='#000000',stroke='none',stroke_width=0))
# Preserve the original custom dash spacing as editable solid path segments,
# rather than accepting the Office preset's different dashes and rounded dots.
for n in list(s['nodes']):
    if n['id']=='sag-library-region':n['dash_pattern']=[11*dx,11*dx]
    if n['shape']!='path' or not n.get('dash_pattern'):continue
    assert n.get('fill')=='none' or n['id']=='sag-library-region'
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
    if n['id']=='sag-library-region':
        # Fill remains a separate native silhouette below the dashed boundary.
        fill=copy.deepcopy(n);fill['id']+='-fill';fill['stroke']='none';fill['dash']=False;fill.pop('dash_pattern');s['nodes'].insert(s['nodes'].index(n),fill);n['fill']='none'
    n['commands']=commands;n['reviewed_source_dash_pattern']=n.pop('dash_pattern');n.pop('dash_phase',None);n['dash_style']='solid';n['dash']=False;n['dash_approximation']='Source dash spacing expanded into editable native solid segments; cubic paths sampled at <=0.4 scene-pixel chord spacing'
s['provenance']['editor_fixes']='Eight reviewed black open shaft/head compounds split to avoid even-odd cutouts. Original individual gradient-arrow pixels precomposed over their verified uniform #F2F2F2 surface while retaining transparent exterior.'
s['provenance']['extraction_review']='Source pixels and final generated PNG inspected; isolated images and rotated text reviewed; independent editor QA pending.'
s['provenance']['text_editability']='Ordinary source captions/labels and reconstructed SAG labels are native typeable text; Timeline is native rotated text. Cambria Math and reconstructed SAG math remain editable glyph paths, not live equations.'
s['provenance']['font_substitutions']='Times New Roman ordinary labels with source weight/italic retained. Reconstructed SAG labels use source-measured Times New Roman sizing.'
s['provenance']['dash_fidelity']='Source custom dash patterns expanded as native solid path segments; no Office dash preset approximation remains in this figure.'
s['provenance']['raster_panel_reconstruction']='Source bitmap instance 38 is not embedded. Its SAG architecture is rebuilt with native shapes/arrows/labels and source mathematical contours. Only flame/snowflake icons and two text-free glow rings are isolated raster insets.'
s['provenance']['extraction_warnings_reviewed']=['All selected source images/shadings isolated with original source SVG clips and masks. Literal letter-M shadow omitted so editing the native instruction does not expose old lettering. SAG bitmap replaced with native objects and isolated icons/glow rings. Rotated ordinary Timeline label restored as native text.']
validate(s,a.out);(a.out/(s['id']+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(s['id'],len(s['nodes']),'objects')
