"""Final source-pixel repairs for RoboSnap, IGen and VLBiMan only."""
import json,sys,subprocess,argparse
from pathlib import Path
import fitz
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from paper_figure.model import validate
from research.prepare_candidate import prepare
p=argparse.ArgumentParser();p.add_argument('slug',choices=['robosnap','igen','vlbiman']);a=p.parse_args();slug=a.slug;D=R/'data/diagrams'/slug;scene=D/(slug+'-figure-2.json');s=json.load(open(scene));papers=json.load(open(R/'data/catalog.json'))['papers'];idx={'robosnap':84,'igen':116,'vlbiman':119}[slug];survey=R/'research/survey'/(papers[idx]['id']+'.json');m=json.load(open(survey))
if slug=='robosnap':
 ids={'pdf-text-96-0','pdf-text-97-0','pdf-text-102-0','pdf-text-104-0','simulation-ready-header'};headers=[n for n in s['nodes']if n['id']in ids];s['nodes']=[n for n in s['nodes']if n['id']not in ids and not n['id'].startswith('source-header-backing-')]
 for j,(x,y,w,h)in enumerate([(84,0,212,70),(541,0,248,71),(923,0,180,49)]):s['nodes'].append(dict(id='source-header-backing-'+str(j),shape='rect',x=x,y=y,width=w,height=h,fill='#FFFFFF',stroke='none',stroke_width=0))
 s['nodes']+=headers;s['provenance']['final_title_gap_repair']='Source white gaps behind all three section titles restored as native white backing shapes; all headings drawn above the original panel borders.'
elif slug=='igen':
 for n in s['nodes']:
  if n['id']in {'plan-line-2-1','plan-line-2-2','plan-line-2-3'} and not s['provenance'].get('final_step3_gap_repair'):n['x']+=7
 s['provenance']['final_step3_gap_repair']='Step3 colored keypoint runs shifted seven additional source-canvas pixels after Lift, giving a clearly visible ordinary word gap independent of trimmed trailing spaces.'
else:
 doc=fitz.open(R/m['pdf_path']);page=doc[3];crop=fitz.Rect(s['provenance']['source_crop_pdf_points']);sc=s['canvas']['width']/crop.width;blocks=[b for b in page.get_text('dict')['blocks']if b['type']==1];paints=[(i,k,b)for i,(k,b)in enumerate(page.get_bboxlog())if k in ['fill-image','fill-shade']];assert len(blocks)==len(paints)==36
 s['nodes']=[n for n in s['nodes']if not(n['id'].startswith(('source-raster-','alpha-photo-','source-pdf-photo-')))]
 for i,b in enumerate(blocks):
  if i in [14,15,32,33,34]:continue # Bitmap header lettering is already live.
  box=fitz.Rect(b['bbox']);assert crop.contains(box)
  pix=fitz.Pixmap(b['image'])
  if b.get('mask'):
   if pix.alpha:pix=fitz.Pixmap(pix,0)
   pix=fitz.Pixmap(pix,fitz.Pixmap(b['mask']))
  name=f'vlbiman-source-pdf-photo-{i}.png'
  # JPEG source RGB is prematted against /Matte before its soft mask. Undo
  # that blend, then save straight RGBA so the original gray tabletop survives.
  import io,re,numpy as np
  from PIL import Image
  raw=Image.open(io.BytesIO(b['image']))
  info=page.get_image_info(xrefs=True)[i];key=doc.xref_get_key(info['xref'],'SMask');matte_key=doc.xref_get_key(int(key[1].split()[0]),'Matte') if key[0]=='xref'else('null','null')
  if b.get('mask')and raw.format=='JPEG'and matte_key[0]=='array':
   rgb=np.asarray(raw.convert('RGB'),dtype=float);alpha=np.asarray(Image.open(io.BytesIO(b['mask'])).convert('L'),dtype=float)/255;matte=np.array([float(v)for v in re.findall(r'[-+]?[0-9]*[.]?[0-9]+',matte_key[1])])*255;straight=np.clip((rgb-matte[None,None,:]*(1-alpha[:,:,None]))/np.maximum(alpha[:,:,None],1/255),0,255).astype('uint8');rgba=np.dstack([straight,np.round(alpha*255).astype('uint8')]);Image.fromarray(rgba).save(D/name)
  else:pix.save(D/name)
  s['nodes'].append(dict(id=f'source-pdf-photo-{i}',shape='image',asset=name,alt='Original PDF image recombined with its own original alpha mask; source photo background and surface texture preserved',x=(box.x0-crop.x0)*sc,y=(box.y0-crop.y0)*sc,width=box.width*sc,height=box.height*sc,source_seqno=paints[i][0]))
 s['nodes'].sort(key=lambda n:n.get('source_seqno',900000))
 n=next(n for n in s['nodes']if n['id']=='phrase-3');n['font_size']=16.5;n['width']=264
 s['provenance']['final_photo_background_repair']='All31 non-header original photo/icon paint instances use original PDF image pixels and own alpha masks in source paint order, reversing source JPEG soft-mask Matte premultiplication to restore pale-gray table surface color/texture omitted by SVG isolated-raster fallback. The long panel2 instances/geometries label is width-fitted at16.5px; all ordinary labels and source arrows remain native.'
validate(s,D);scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True);print(prepare(slug,survey,scene,R/'build'/slug,D/(s['id']+'-original.png')))
