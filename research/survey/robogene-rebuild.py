slug='robogene'
import argparse,json,sys,subprocess,fitz,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();cfg=json.load(open(R/'research/survey'/f'{slug}-config.json'));out=R/'data/diagrams'/slug;cfg_native=dict(cfg,reviewed_raw_images=[],raster_regions=[]);s=extract(Path(a.pdf),cfg_native,out);page=fitz.open(a.pdf)[cfg['page']-1];crop=fitz.Rect(cfg['crop']);scale=cfg['scale'];backgrounds=[]
def panel(id,b,fill,stroke='#18323D',radius=6):
 r=fitz.Rect(b);w=r.width*scale;h=r.height*scale;rad=radius*scale
 n={'id':id,'shape':'path','x':(r.x0-crop.x0)*scale,'y':(r.y0-crop.y0)*scale,'width':w,'height':h,'fill':fill,'stroke':stroke,'stroke_width':1.2,'commands':[{'moveTo':{'x':rad,'y':0}},{'lineTo':{'x':w-rad,'y':0}},{'quadBezTo':{'x1':w,'y1':0,'x':w,'y':rad}},{'lineTo':{'x':w,'y':h-rad}},{'quadBezTo':{'x1':w,'y1':h,'x':w-rad,'y':h}},{'lineTo':{'x':rad,'y':h}},{'quadBezTo':{'x1':0,'y1':h,'x':0,'y':h-rad}},{'lineTo':{'x':0,'y':rad}},{'quadBezTo':{'x1':0,'y1':0,'x':rad,'y':0}},{'close':{}}]};backgrounds.append(n)

for k,b,fill in [(3,[374.2,61.8,452.3,108.4],'#E8E1ED'),(6,[162.1,137.5,249.4,237.1],'#E5EEE5'),(9,[80.5,60.8,148.1,111.2],'#DCEAF7'),(14,[171.6,60.8,242.3,109.7],'#E5EEE5'),(17,[264.8,60.8,334.6,111.1],'#DCEAF7'),(20,[164.1,243.7,234.1,293.4],'#DCEAF7'),(23,[293.5,243.7,366.3,293.3],'#E5EEE5'),(31,[73.8,137.5,161.3,237.1],'#E5EEE5'),(38,[408.3,235.6,520.1,294.4],'#F7ECE8'),(40,[250,137.5,337.3,236.5],'#E5EEE5'),(48,[375.2,120.2,540.1,174.8],'#E8E1E5'),(59,[403,185,525,229],'#F8F8F8')]:panel('native-panel-'+str(k),b,fill,radius=11 if k in [6,31,40]else 7)
# Insert background cards after the two original full-page colored panel fills, before paths/text.
s['nodes']=s['nodes'][:2]+backgrounds+s['nodes'][2:]
# The only rotated ordinary label is Retrieve, positioned natively along the dashed memory route.
rot=[n for n in s['nodes']if n['shape']=='text'and n.get('source_seqno') in {sp['seqno']for sp in page.get_texttrace()if tuple(sp.get('dir',(1,0)))!=(1,0)}]
if rot:
 ids={n['id']for n in rot};s['nodes']=[n for n in s['nodes']if n['id']not in ids];s['nodes'].append({'id':'retrieve-live','shape':'text','label':'Retrieve','x':855,'y':231,'width':92,'height':18,'rotation':90,'font_size':18,'font_family':'Times New Roman','bold':True,'align':'center','text_inset':0,'no_wrap':True})
s['provenance']['notes']+=' Native rounded panels replace source bitmap panels; broad bitmap drop shadows omitted. Reviewed icon clipping removes source duplicate hidden fragments. Gradient card fill approximated with uniform native fills.'

for n in s['nodes']:
 if n['id']=='native-panel-3':n['dash_style']='dashed';n['dash']=True
 if n['id']=='native-panel-59':
  w,h=n['width'],n['height'];n['commands']=[{'moveTo':{'x':0,'y':0}},{'lineTo':{'x':w-42,'y':0}},{'lineTo':{'x':w,'y':20}},{'lineTo':{'x':w,'y':h-24}},{'lineTo':{'x':w-48,'y':h}},{'lineTo':{'x':0,'y':h}},{'close':{}}]
 if n.get('label')=='Generate Key':n['label']='Generate Key-Value Pair';n['width']=230;n['font_size']=20
# Isolate all non-panel source image paints with the original SVG clip/mask
# chain. This preserves complete robot ears/bases, articulated robot-arm links,
# scene stack photographs, and the small three-arm data-collection group.
import copy,tempfile,os
from lxml import etree as ET
from PIL import Image
svg=ET.fromstring(page.get_svg_image(text_as_path=True).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs')
images=page.get_image_info();paints=[(i,k,fitz.Rect(b)) for i,(k,b) in enumerate(page.get_bboxlog()) if k in ['fill-image','fill-shade']]
elements=[e for e in svg.iter() if (e.tag.rsplit('}',1)[-1]=='image' or (e.tag.rsplit('}',1)[-1]=='use' and e.get('data-text') is None)) and not any(p.tag.rsplit('}',1)[-1]=='defs' for p in e.iterancestors())]
assert len(images)==len(paints)==len(elements)==67
omit=set(cfg['reviewed_omitted_or_rebuilt_image_indices'])
with tempfile.TemporaryDirectory(prefix='robogene-exact-images-') as tmp:
 for i,(element,b,(seq,kind,_)) in enumerate(zip(elements,images,paints)):
  if i in omit:continue
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
  src=Path(tmp)/f'{i}.svg';src.write_bytes(ET.tostring(isolated));name=f'robogene-source-component-{i}.png'
  subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(R/'research/render-isolated-svg.cjs'),str(src),str(out/name)],check=True,env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES','')),stdout=subprocess.DEVNULL)
  im=Image.open(out/name).convert('RGBA');ab=im.getchannel('A').getbbox()
  if ab is None:continue
  x0,y0,x1,y1=ab;px=rect.width/im.width;py=rect.height/im.height;im.crop(ab).save(out/name);rr=fitz.Rect(rect.x0+x0*px,rect.y0+y0*py,rect.x0+x1*px,rect.y0+y1*py)
  s['nodes'].append(dict(id=f'robogene-exact-source-{i}',shape='image',asset=name,alt='Individual original photograph or icon, preserving exact source mask, crop, affine transform and visible silhouette',x=(rr.x0-crop.x0)*scale,y=(rr.y0-crop.y0)*scale,width=rr.width*scale,height=rr.height*scale,source_seqno=seq))
# Reinsert native substitute backgrounds ahead of their source foreground paints.
for n in backgrounds:n['source_seqno']=(paints[35][0]-.1 if n['id']=='native-panel-59' else paints[int(n['id'].rsplit('-',1)[-1])][0])
document_panel=next(n for n in backgrounds if n['id']=='native-panel-59');w,h=document_panel['width'],document_panel['height']
s['nodes'].append(dict(id='robogene-document-native-folds',shape='path',x=document_panel['x'],y=document_panel['y'],width=w,height=h,fill='none',stroke='#18323D',stroke_width=1.2,source_seqno=document_panel['source_seqno']+.01,commands=[{'moveTo':{'x':w-42,'y':0}},{'lineTo':{'x':w-42,'y':20}},{'lineTo':{'x':w,'y':20}},{'moveTo':{'x':0,'y':20}},{'lineTo':{'x':w-42,'y':20}},{'moveTo':{'x':w-48,'y':h}},{'lineTo':{'x':w-48,'y':h-24}},{'lineTo':{'x':w,'y':h-24}}]))
s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
s['provenance']['notes']+=' Updated exact isolated SVG image extraction restores full robot-icon silhouettes and the articulated three-arm collection illustration. Photo stacks and clipped sprite icons follow original source paint order; only reviewed bitmap panels and shadows are replaced/omitted.'
# Use measured native inter-run spacing in the task document. Source Skeena
# metrics differ from the editable Arial replacement, so fit the bold prefixes
# and keep a real visual word-space before each independently editable value.
font_bold=fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf')
font_regular=fitz.Font(fontfile='/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf')
by_id={n['id']:n for n in s['nodes']}
location=by_id['pdf-text-93-0'];following=by_id['pdf-text-94-0'];location['label']='Location Information: ';location['width']=following['x']+following['width']-location['x'];s['nodes'].remove(following)
for prefix_id,value_id in [('pdf-text-85-0','pdf-text-86-0'),('pdf-text-87-0','pdf-text-88-0'),('pdf-text-89-0','pdf-text-90-0'),('pdf-text-91-0','pdf-text-92-0'),('pdf-text-93-0','pdf-text-95-0')]:
 prefix=by_id[prefix_id];value=by_id[value_id];end=value['x']+value['width'];gap=3.5
 measured=font_bold.text_length(prefix['label'].rstrip(),fontsize=prefix['font_size']);prefix['font_size']*=min(1,(prefix['width']-gap)/max(measured,.01))
 value['x']=prefix['x']+font_bold.text_length(prefix['label'].rstrip(),fontsize=prefix['font_size'])+gap;value['width']=end-value['x']
 measured=font_regular.text_length(value['label'],fontsize=value['font_size']);value['font_size']*=min(1,value['width']/max(measured,.01))
f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
