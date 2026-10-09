"""Paper-specific extraction and masked source components for discovery queue."""
import argparse,json,sys,copy,os,subprocess,tempfile,math,re
from pathlib import Path
import fitz
from lxml import etree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from paper_figure.pdf_extract import extract
from paper_figure.model import validate
PAPERS={49:'vergsa',50:'dodont',57:'deep-skill-chaining',58:'mobile-skill',109:'host',125:'dreamgen',127:'dexmimicgen',126:'demogen'}
p=argparse.ArgumentParser();p.add_argument('index',type=int);a=p.parse_args();slug=PAPERS[a.index];papers=json.load(open(ROOT/'data/catalog.json'))['papers'];m=json.load(open(ROOT/'research/survey'/(papers[a.index]['id']+'.json')));f=m['figure_candidates'][0]
if a.index==126:f={'figure':'Figure 1','page_1_based':1,'crop_pdf_points':[49,181,562,397]}
crop=f['crop_pdf_points']
if a.index==58:crop=[78,204,271,444]
c={'id':slug+'-figure-'+f['figure'].split()[-1],'paper_title':m['title_expected'],'paper_url':m['source_url'],'figure':f['figure'],'page':f['page_1_based'],'crop':crop,'scale':3,'license':m.get('license_note','unverified'),'notes':'Source-layout reconstruction using native PDF paths and live ordinary labels. Each source photograph, illustration or mathematical bitmap is an isolated insert with original clipping. No whole-figure raster backdrop. Native paths are not semantically attached connectors.','outline_fonts':['CMM','CMSY','CMEX','CambriaMath']+(['STIXGeneral'] if a.index==125 else [])}
out=ROOT/'data/diagrams'/slug;out.mkdir(parents=True,exist_ok=True);config=ROOT/'research/configs'/(slug+'.json');config.write_text(json.dumps(c,indent=2)+'\n');pdf=ROOT/m['pdf_path'];s=extract(pdf,c,out);doc=fitz.open(pdf);page=doc[c['page']-1];crop=fitz.Rect(c['crop']);scale=c['scale']
blocks=[b for b in page.get_text('dict')['blocks']if b['type']==1];paints=[(i,k,fitz.Rect(b))for i,(k,b)in enumerate(page.get_bboxlog())if k in ['fill-image','fill-shade']]
svg=ET.fromstring(page.get_svg_image(text_as_path=True).encode());defs=svg.find('{http://www.w3.org/2000/svg}defs');elements=[e for e in svg.iter()if(e.tag.rsplit('}',1)[-1]=='image'or(e.tag.rsplit('}',1)[-1]=='use'and e.get('data-text')is None))and not any(a.tag.rsplit('}',1)[-1]=='defs'for a in e.iterancestors())];assert len(elements)==len(blocks)==len(paints),(len(elements),len(blocks),len(paints))
with tempfile.TemporaryDirectory(prefix=slug+'-source-')as tmp:
 for i,(element,b,(seq,kind,_))in enumerate(zip(elements,blocks,paints)):
  rect=fitz.Rect(b['bbox'])&crop
  if rect.is_empty:continue
  isolated=ET.Element(svg.tag,nsmap=svg.nsmap,**dict(svg.attrib));isolated.append(copy.deepcopy(defs));isolated.set('width',str(rect.width));isolated.set('height',str(rect.height));isolated.set('viewBox',f'{rect.x0} {rect.y0} {rect.width} {rect.height}')
  chain=[];parent=element.getparent()
  while parent is not None and parent is not svg:chain.append(parent);parent=parent.getparent()
  cursor=isolated
  for ancestor in reversed(chain):child=ET.Element(ancestor.tag,**dict(ancestor.attrib));cursor.append(child);cursor=child
  if element.tag.rsplit('}',1)[-1]=='use':
   ref=element.get('{http://www.w3.org/1999/xlink}href')[1:];resolved=copy.deepcopy(svg.xpath('//*[@id=$id]',id=ref)[0]);attrs={k:v for k,v in element.attrib.items()if not k.endswith('href')}
   if attrs:child=ET.Element('{http://www.w3.org/2000/svg}g',**attrs);cursor.append(child);cursor=child
   cursor.append(resolved)
  else:cursor.append(copy.deepcopy(element))
  src=Path(tmp)/(str(i)+'.svg');src.write_bytes(ET.tostring(isolated));name=f'{slug}-source-component-{i}.png';subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'research/render-isolated-svg.cjs'),str(src),str(out/name)],check=True,env=dict(os.environ,NODE_PATH=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES','')),stdout=subprocess.DEVNULL)
  s['nodes'].append(dict(id=f'{slug}-source-component-{i}',shape='image',asset=name,alt='Individual original source image with original source SVG clipping and mask; internal pixels are raster',x=(rect.x0-crop.x0)*scale,y=(rect.y0-crop.y0)*scale,width=rect.width*scale,height=rect.height*scale,source_seqno=seq))
# Restore rotated source labels, keeping each label as one typeable object.
rotated=[span for span in page.get_texttrace()if span['dir']!=(1.,0.)and crop.contains(fitz.Rect(span['bbox']))];rotated_seq={span['seqno']for span in rotated};s['nodes']=[n for n in s['nodes']if not(n['shape']=='text'and n.get('source_seqno')in rotated_seq)]
for span in rotated:
 r=fitz.Rect(span['bbox']);x=(r.x0-crop.x0)*scale;y=(r.y0-crop.y0)*scale;w=r.width*scale;h=r.height*scale;label=''.join(chr(ch[0])for ch in span['chars']);rotation=round(math.degrees(math.atan2(span['dir'][1],span['dir'][0])))%360
 s['nodes'].append(dict(id=f'{slug}-rotated-label-{span["seqno"]}',shape='text',label=label,x=x+(w-h)/2,y=y+(h-w)/2,width=h,height=w,rotation=rotation,font_size=span['size']*scale,font_family='Arial',align='center',text_color='#000000',no_wrap=True,text_inset=0,source_seqno=span['seqno']))
for n in s['nodes']:
 if n['shape']=='text':
  n['bold']=n.get('bold',False) or any(v in n.get('source_font','') for v in ['Heavy','Black']);n['label']=n['label'].replace('ﬁ','fi').replace('ﬂ','fl');n['italic']=n.get('italic',False)or'Ital'in n.get('source_font','')
  fam=n.get('font_family','Arial');is_times=fam=='Times New Roman';font=('tibi'if n.get('italic')and n.get('bold')else'tibo'if n.get('bold')else'tiit'if n.get('italic')else'tiro')if is_times else('hebi'if n.get('italic')and n.get('bold')else'hebo'if n.get('bold')else'heit'if n.get('italic')else'helv')
  old=n['font_size'];length=fitz.get_text_length(n['label'],fontname=font,fontsize=old);n['font_size']*=min(1,n['width']/max(length,.01))
  if not n.get('rotation'):n['y']=max(0,n['y']-.15*old+.5*(old-n['font_size']))
  else:n['x']-=.15*old
s['provenance']['extraction_warnings_reviewed']=['Raster warnings resolved by independently isolated source SVG image instances with original masks/clips and source paint order. Native source clipping and preview compared against original pixels. Rotated ordinary labels restored as native rotated text. Full-figure crop-crossing white backgrounds intentionally omitted. PDF dash lengths approximate nearest native PowerPoint preset.'];s['nodes'].sort(key=lambda n:n.get('source_seqno',1000000))
if a.index==50:
 left=next(n for n in s['nodes']if n['id']=='pdf-text-39-0');right=next(n for n in s['nodes']if n['id']=='pdf-text-40-0');left['label']='Instruction reward';left['width']=right['x']+right['width']-left['x'];s['nodes']=[n for n in s['nodes']if n['id']!=right['id']]
s['provenance']['text_editability']='Ordinary source labels are live text; selected mathematical fonts are native outlines. Source image inserts retain internal raster pixels.'
s['provenance']['image_reconstruction']='Each source raster instance is isolated with complete source SVG ancestry, source clipping, mask and paint order. No full-figure image is used.'
validate(s,out);scene=out/(s['id']+'.json');scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(slug,len(s['nodes']),flush=True);subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(ROOT/'build'/slug),'--preview','--force'],cwd=ROOT,check=True)
