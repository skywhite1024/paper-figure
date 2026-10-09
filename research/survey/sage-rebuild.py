import argparse,json,math,sys,subprocess,fitz
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();slug='sage';cfg=json.load(open(R/'research/survey'/f'{slug}-config.json'));out=R/'data/diagrams'/slug;s=extract(Path(a.pdf),cfg,out);page=fitz.open(a.pdf)[cfg['page']-1];crop=fitz.Rect(cfg['crop']);scale=cfg['scale'];seen=set();seqs=set();rotated=[]
for span in page.get_texttrace():
 if tuple(span.get('dir',(1,0)))==(1,0) or not crop.contains(fitz.Rect(span['bbox'])):continue
 seqs.add(span['seqno']);label=''.join(chr(c[0])for c in span['chars']);b=fitz.Rect(span['bbox']);key=(label,tuple(b))
 if key in seen:continue
 seen.add(key);dx,dy=span['dir'];rotation=math.degrees(math.atan2(dy,dx));h=span['size']*scale;w=max(h,(b.width*scale-h*abs(dy))/abs(dx));cx=((b.x0+b.x1)/2-crop.x0)*scale;cy=((b.y0+b.y1)/2-crop.y0)*scale
 rotated.append({'id':'rotated-'+str(span['seqno']),'shape':'text','x':cx-w/2,'y':cy-h/2,'width':w,'height':h,'rotation':rotation,'label':label,'font_size':h,'font_family':'Arial','fill':'none','stroke':'none','text_color':'#000000','text_inset':0,'no_wrap':True,'align':'center'})
s['nodes']=[n for n in s['nodes']if not(n['shape']=='text'and n.get('source_seqno')in seqs)]+rotated
s['provenance']['notes']+=' Rotated labels reconstructed as native typeable text, duplicated PDF fill/stroke spans deduplicated. Four clipped room/photo insets restored at reviewed source-visible bounds. Photographic interiors and illustrated avatars remain raster assets.'
f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
