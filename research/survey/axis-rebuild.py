"""Reproduce this inspected paper figure with live labels and native PDF geometry.
Original raster image/shading objects are isolated individually with their source
SVG transforms, clipping and alpha. No full-figure image is used as a backdrop.
"""
import json,hashlib,subprocess,sys,copy,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from lxml import etree
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from paper_figure.pdf_extract import extract
from research.prepare_candidate import prepare
SLUG='axis';CAT='axis-a-growable-community-driven-data-engine-for-scalable-robot-manipulation'
evpath=R/'research/survey'/f'{CAT}.json';ev=json.loads(evpath.read_text());pdf=R/ev['pdf_path'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(pdf)==ev['pdf_sha256']
D=R/'data/diagrams'/SLUG;B=R/'build'/SLUG;B.mkdir(parents=True,exist_ok=True);C=R/'build/candidates'/SLUG
cfg=json.loads((R/'research/survey'/f'{SLUG}-config.json').read_text());s=extract(pdf,cfg,D);scene=D/(s['id']+'.json');page=fitz.open(pdf)[cfg['page']-1];crop=fitz.Rect(cfg['crop']);sc=cfg['scale'];nodes=s['nodes'];logs=page.get_bboxlog()
# Original raster assets are not rectangular screenshots: preserve exact source clips.
svg=etree.fromstring(page.get_svg_image(text_as_path=True).encode(),etree.XMLParser(recover=True));tag=lambda e:e.tag.rsplit('}',1)[-1]
ids={e.get('id') for e in svg.iter() if tag(e)=='image'}
instances=[e for e in svg.iter() if (tag(e)=='image' or tag(e)=='use' and e.get('{http://www.w3.org/1999/xlink}href','')[1:] in ids) and not any(tag(a)=='defs' for a in e.iterancestors())]
image_logs=[(seq,fitz.Rect(bb)) for seq,(kind,bb) in enumerate(logs) if kind in ('fill-image','fill-shade')]
assert len(instances)==len(image_logs),(len(instances),len(image_logs))
jobs=[]
for i,(element,(seq,box)) in enumerate(zip(instances,image_logs)):
 if not box.intersects(crop):continue
 if i in cfg.get('skip_raster_indices',[]):continue
 if any(fitz.Rect(r['bbox']).contains(box & crop) for r in cfg.get('raster_regions',[])):continue
 iso=copy.deepcopy(svg);allinst=[e for e in iso.iter() if (tag(e)=='image' or tag(e)=='use' and e.get('{http://www.w3.org/1999/xlink}href','')[1:] in ids) and not any(tag(a)=='defs' for a in e.iterancestors())];target=allinst[i]
 for e in list(iso.iter()):
  if e is iso or any(tag(a)=='defs' for a in e.iterancestors()) or tag(e) in ('svg','defs','g','mask','clipPath'):continue
  if e is not target and e.getparent() is not None:e.getparent().remove(e)
 iso.set('viewBox',' '.join(map(str,cfg['crop'][:2]+[crop.width,crop.height])));iso.set('width',str(crop.width*sc));iso.set('height',str(crop.height*sc))
 fn=B/f'isolated-raster-{i}.svg';fn.write_bytes(etree.tostring(iso));jobs.append([str(fn),str(B/f'isolated-raster-{i}.png'),i,seq])
js="const fs=require('fs'),sharp=require('sharp'); (async()=>{for(const j of JSON.parse(fs.readFileSync(process.argv[1]))){await sharp(fs.readFileSync(j[0])).png().toFile(j[1]);}})().catch(e=>{console.error(e);process.exit(1)});"
(B/'raster-jobs.json').write_text(json.dumps(jobs));subprocess.run(['node','-e',js,str(B/'raster-jobs.json')],check=True,cwd=R)
for _,png,i,seq in jobs:
 im=Image.open(png).convert('RGBA');box=im.getchannel('A').getbbox()
 if not box:continue
 name=f'{SLUG}-source-raster-{i}.png';im.crop(box).save(D/name)
 nodes.append({'id':f'source-raster-{i}','shape':'image','label':'','asset':name,'alt':'Isolated original photo/rendering/icon/shading asset; original source transparency and clip retained; internal pixels remain raster','x':box[0],'y':box[1],'width':box[2]-box[0],'height':box[3]-box[1],'source_seqno':seq})
s['nodes']=sorted(nodes,key=lambda n:n.get('source_seqno',100000))
# PAPER_SPECIFIC_POSTPROCESS
# The diagnostic 3-d0 trajectory plot is reconstructed natively as well: grid,
# trajectory samples, axes, colored time strip and every tick/legend label.
# Coordinates were traced from the inspected original chart inset.
s['nodes']=[n for n in s['nodes'] if n['id'] not in ['source-raster-1','source-raster-2'] and n.get('source_seqno')!=23]
plot=[]
def xy(p):return ((391+p[0]/7-crop.x0)*sc,(260+p[1]/7-crop.y0)*sc)
def pl(id,pts,col='#DCDCDC',width=.27,fill='none',close=False):
 pts=[xy(p) for p in pts];x=min(p[0] for p in pts);y=min(p[1] for p in pts);cs=[{'moveTo':{'x':pts[0][0]-x,'y':pts[0][1]-y}}]+[{'lineTo':{'x':u-x,'y':v-y}} for u,v in pts[1:]]
 if close:cs.append({'close':{}})
 plot.append({'id':id,'shape':'path','label':'','x':x,'y':y,'width':max(.01,max(p[0] for p in pts)-x),'height':max(.01,max(p[1] for p in pts)-y),'commands':cs,'fill':fill,'stroke':col,'stroke_width':width,'source_seqno':32})
def tx(id,t,p,fs=4,col='#666666',rot=0):
 x,y=xy(p);plot.append({'id':id,'shape':'text','label':t,'x':x,'y':y,'width':16,'height':5,'font_size':fs,'font_family':'Arial','text_color':col,'align':'left','text_inset':0,'no_wrap':True,'rotation':rot,'source_seqno':32})
def mix(a,b,t):return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
a0=(174,343);b0=(418,417);c0=(539,304);d0=(310,232);At=(170,165);Dt=(310,62);Ct=(539,139)
for j in range(11):
 t=j/10
 pl(f'plot-floor-x-{j}',[mix(a0,b0,t),mix(d0,c0,t)])
 pl(f'plot-floor-y-{j}',[mix(a0,d0,t),mix(b0,c0,t)])
 pl(f'plot-back-vertical-{j}',[mix(d0,c0,t),mix(Dt,Ct,t)])
 pl(f'plot-left-vertical-{j}',[mix(a0,d0,t),mix(At,Dt,t)])
 if j<10:
  pl(f'plot-back-z-{j}',[mix(d0,Dt,t),mix(c0,Ct,t)])
  pl(f'plot-left-z-{j}',[mix(a0,At,t),mix(d0,Dt,t)])
for j in range(10):
 p=mix(a0,b0,j/9);tx(f'plot-x-tick-{j}',f'{.30+j*.05:.2f}',(p[0]-8,p[1]+3),2.8)
 p=mix(b0,c0,j/9);tx(f'plot-y-tick-{j}',f'{-.30+j*.05:.2f}',(p[0]+4,p[1]-2),2.8)
 if j<9:
  p=mix(c0,Ct,(j+1)/9);tx(f'plot-z-tick-{j}',f'{.05+j*.05:.2f}',(p[0]+5,p[1]-2),2.8)
tx('plot-x-axis','X (m)',(274,395),3.3);tx('plot-y-axis','Y (m)',(482,352),3.3,rot=315);tx('plot-z-axis','Z (m)',(555,203),3.3,rot=270)
trace=[(289,88),(308,93),(327,98),(349,103),(370,108),(386,116),(401,130),(416,145),(429,161),(435,181),(440,202),(444,220),(451,235),(460,245),(472,252),(480,266),(484,287),(486,314),(487,292),(485,267),(478,248),(462,242),(449,247),(435,261),(421,273)]
colors=['#1300A8','#1900AE','#2500B4','#3300AE','#4D00A0','#660092','#7D0084','#980078','#B00066','#C80050','#DD0038','#EF0020','#FF1600','#FF2C00','#FF4900','#FF6800','#FF8500','#FFA000','#FFB700','#FFCC00','#FFDF00','#FFF000','#FFFF00','#FFFF00']
for j,(a,b) in enumerate(zip(trace,trace[1:])):
 pl(f'trajectory-segment-{j}',[a,b],colors[j],1.05)
 for k in range(3):
  p=mix(a,b,k/3);x,y=xy(p);plot.append({'id':f'trajectory-sample-{j}-{k}','shape':'ellipse','label':'','x':x-.6,'y':y-.6,'width':1.2,'height':1.2,'fill':colors[j],'stroke':'none','source_seqno':32})
for j,p in enumerate([(289,87),(386,114),(432,166),(436,187),(446,225),(461,257),(477,288),(486,306),(487,323),(485,250)]):
 x,y=xy(p);plot.append({'id':f'original-red-sample-{j}','shape':'ellipse','label':'','x':x-.5,'y':y-.5,'width':1,'height':1,'fill':'#DE1B18','stroke':'none','source_seqno':32})
pl('plot-start-marker',[(286,85),(294,88),(287,92)],'#65AA9D',0,'#65AA9D',True);pl('plot-end-a',[(417,270),(425,276)],'#202020',.8);pl('plot-end-b',[(417,276),(425,270)],'#202020',.8)
# Sixty-four native rectangles approximate the original diagnostic color strip.
stops=['#1300AD','#6700BB','#B60084','#E51427','#FF7600','#FFD800','#FFFF00']
def grad(t):
 k=min(len(stops)-2,int(t*(len(stops)-1)));u=t*(len(stops)-1)-k;a=stops[k];b=stops[k+1];return '#'+''.join(f'{round(int(a[j:j+2],16)*(1-u)+int(b[j:j+2],16)*u):02X}' for j in [1,3,5])
for j in range(64):
 x,y=xy((584,68+j*345/64));plot.append({'id':f'time-strip-{j}','shape':'rect','label':'','x':x,'y':y,'width':17/7*sc,'height':345/64/7*sc+.4,'fill':grad(1-j/63),'stroke':'none','source_seqno':17})
# Paint chart before native source legend and the remaining source annotations.
s['nodes']=sorted(s['nodes']+plot,key=lambda n:n.get('source_seqno',100000))
b=fitz.Rect(479.1443,288.3974,480.9173,304.4578);cx=(b.x0+b.x1)/2;cy=(b.y0+b.y1)/2;w=b.height*sc;h=b.width*sc
s['nodes'].append({'id':'simulation-times-label','shape':'text','label':'Simulation Times (s)','x':(cx-crop.x0)*sc-w/2,'y':(cy-crop.y0)*sc-h/2,'width':w,'height':h,'font_size':5.3,'font_family':'Arial','text_color':'#111111','align':'center','text_inset':0,'no_wrap':True,'rotation':90})
# Merge source ligature-split headings into clean live words.
for seqs,label in [([5,6,7,8,9],'Offline Data Cleaning & Refinement'),([51,52,53],'Refined Trajectories')]:
 ns=[n for n in s['nodes'] if n['shape']=='text' and n.get('source_seqno') in seqs]
 if ns:
  n=dict(ns[0]);n['label']=label;n['x']=min(z['x'] for z in ns);n['width']=max(z['x']+z['width'] for z in ns)-n['x'];n['id']='merged-source-heading-'+str(seqs[0]);s['nodes']=[z for z in s['nodes'] if z not in ns];s['nodes'].append(n)
for n in s['nodes']:
 if n['shape']=='text' and not n.get('rotation'):
  font='hebo' if n.get('bold') else 'helv';length=fitz.get_text_length(n['label'],fontname=font,fontsize=n['font_size'])
  if length>n['width']:n['font_size']*=n['width']/length*.98
s['provenance']['notes']+=' Diagnostic 3-d0 plot reconstructed natively from visually traced source geometry: native grid, trajectories, sample markers, ticks and segmented time color strip. Plot tracing and color gradient are approximate; no raster chart retained.'

s['provenance']['notes']+=' Original raster assets isolated with their exact original alpha, clipping and affine transforms; no full-figure raster backdrop.'
s['provenance']['original_extraction_warnings']=s['provenance'].get('extraction_warnings',[])
s['provenance']['extraction_warnings']=[w for w in s['provenance'].get('extraction_warnings',[]) if not w.startswith('unhandled image/shading')]
s['provenance']['raster_boundaries']=[{'id':n['id'],'bounds_canvas':[n[k] for k in ['x','y','width','height']],'detail':n['alt']} for n in s['nodes'] if n['shape']=='image']
scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(B),'--preview','--force'],cwd=R,check=True)
prepare(SLUG,evpath,scene,B,D/(s['id']+'-original.png'))
with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
v={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source inspected; generated preview comparison pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(n.get('label')) for n in s['nodes']),'native_paths':sum(n['shape']=='path' for n in s['nodes']),'raster_images':sum(n['shape']=='image' for n in s['nodes']),'raster_boundaries':s['provenance']['raster_boundaries']},'limitations':['Native geometry retained; font metrics, dashes, arrow rendering may vary','Native paths are editable but lack automatic semantic attachment','No PowerPoint or draw.io GUI editing validation claimed']}
(C/'VALIDATION.json').write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');print(SLUG,counts)
