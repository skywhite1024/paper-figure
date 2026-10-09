"""Rebuild URSA with source photo clipping and typeable labels fitted to original spans."""
import argparse,json,subprocess,sys,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/ursa';cfg=r/'research/survey/ursa-config.json'
subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(cfg),'--out',str(out)],check=True);f=out/'ursa-figure-2.json';s=json.loads(f.read_text())
for n in s['nodes']:
 if n['shape']=='text' and n.get('source_font')=='Helvetica':n['font_size']=min(n['font_size'],n['width']/max(.1,fitz.Font('helv').text_length(n['label'],fontsize=1)))

for n in s['nodes']:
 if n.get('label','').startswith('No addition to repertoire'):n['font_size']*=.9
s['provenance']['notes']+=' Ordinary text width-fitted to original source boxes; source math gradient glyphs remain tiny raster assets.';f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/ursa'),'--preview','--force'],cwd=r,check=True)
