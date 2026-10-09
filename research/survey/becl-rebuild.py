"""Rebuild BeCL with native typeable ordinary labels and original image subassets."""
import argparse,json,subprocess,sys,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/becl';cf=r/'research/survey/becl-config.json';cfg=json.loads(cf.read_text());subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(cf),'--out',str(out)],check=True);f=out/(cfg['id']+'.json');s=json.loads(f.read_text());s['nodes']=[n for n in s['nodes'] if n.get('source_font')!='Calibri'];crop=fitz.Rect(cfg['crop']);scale=cfg['scale'];pg=fitz.open(a.pdf)[cfg['page']-1];k=0
for b in pg.get_text('dict',clip=crop)['blocks']:
 if 'lines' not in b:continue
 for line in b['lines']:
  for v in line['spans']:
   if v['font']!='Calibri' or not v['text'].strip():continue
   x0,y0,x1,y1=v['bbox'];k+=1;label=v['text'];s['nodes'].append({'id':f'becl-live-label-{k}','shape':'text','label':label,'x':(x0-crop.x0)*scale,'y':(y0-crop.y0)*scale,'width':(x1-x0)*scale+1,'height':(y1-y0)*scale,'font_size':min(v['size'],(x1-x0)/max(.1,fitz.Font('helv').text_length(label,fontsize=1)))*scale,'font_family':'Arial','text_color':f'#{v["color"]:06X}','align':'left','text_inset':0,'no_wrap':True,'source_font':'Calibri','source_note':'Typeable source span, width-fitted Arial replacement'})

for n in s['nodes']:
 if n.get('label','').startswith('Two trajectories from skill'):n['font_size']*=.94
s['provenance']['notes']+=f' {k} ordinary Calibri label spans restored as typeable text; only mathematical symbols remain glyph paths.';f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/becl'),'--preview','--force'],cwd=r,check=True)
