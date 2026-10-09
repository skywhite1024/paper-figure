"""APS Figure 2: split seven reviewed overlapping arrow shaft/head compounds for Office parity."""
import argparse,json,subprocess,sys,copy,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/aps'
subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(r/'research/survey/aps-config.json'),'--out',str(out)],check=True)
f=out/'aps-figure-2.json';s=json.loads(f.read_text());nodes=[]
for n in s['nodes']:
 if n['id'] not in ['pdf-path-7','pdf-path-11','pdf-path-22','pdf-path-23','pdf-path-27','pdf-path-28','pdf-path-29']:nodes.append(n);continue
 segments=[]
 for c in n['commands']:
  if 'moveTo'in c:segments.append([])
  segments[-1].append(c)
 for j,seg in enumerate(segments):
  nn=copy.deepcopy(n);nn['id']+=f'-part-{j}';nn['commands']=seg;nodes.append(nn)
nodes=[n for n in nodes if n.get('source_font')!='Calibri']
cfg=json.loads((r/'research/survey/aps-config.json').read_text());crop=fitz.Rect(cfg['crop']);scale=cfg['scale'];pg=fitz.open(a.pdf)[cfg['page']-1];k=0
for b in pg.get_text('dict',clip=crop)['blocks']:
 if 'lines' not in b:continue
 for line in b['lines']:
  for span in line['spans']:
   if span['font']!='Calibri' or not span['text'].strip():continue
   x0,y0,x1,y1=span['bbox'];k+=1
   nodes.append({'id':f'aps-typeable-label-{k}','shape':'text','label':span['text'].strip(),'x':(x0-crop.x0)*scale,'y':(y0-crop.y0)*scale,'width':(x1-x0)*scale+2,'height':(y1-y0)*scale,'font_size':min(span['size'],(x1-x0)/fitz.Font('helv').text_length(span['text'],fontsize=1))*scale,'font_family':'Arial','text_color':'#000000','align':'left','text_inset':0,'no_wrap':True,'source_font':'Calibri','source_note':'Typeable whole source span with original word spacing'})
fixed=[]
for n in nodes:
 if n.get('label','').startswith('Pre-Trained'):
  for j,label in enumerate(['Pre-Trained','Successor Features']):
   rect=next(b for b in pg.search_for(label) if crop.contains(b));nn=copy.deepcopy(n);nn['id']+=f'-{j}';nn['label']=label;nn['x']=(rect.x0-crop.x0)*scale;nn['width']=rect.width*scale+1;nn['font_size']=min(span['size'],rect.width/fitz.Font('helv').text_length(label,fontsize=1))*scale;fixed.append(nn)
 else:fixed.append(n)
s['nodes']=fixed;s['provenance']['notes']+=' Ordinary Calibri labels reconstructed as16typeable text objects; only mathematical symbols outlined. ';s['provenance']['notes']+=' Seven reviewed filled arrow shaft/head compound paths split into independent native subpaths to preserve solid arrow joins under Office even-odd fill.';f.write_text(json.dumps(s,indent=2))
subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/aps'),'--preview','--force'],cwd=r,check=True)
