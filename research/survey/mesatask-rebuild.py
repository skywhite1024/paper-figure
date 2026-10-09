import argparse,json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();slug='mesatask';cfg=json.load(open(R/'research/survey'/f'{slug}-config.json'));out=R/'data/diagrams'/slug;s=extract(Path(a.pdf),cfg,out)
import fitz
for n in s['nodes']:
 if n['shape']=='text':
  font='hebo' if n.get('bold') else 'helv';length=fitz.get_text_length(n['label'],fontname=font,fontsize=n['font_size'])
  if length>n['width']:n['font_size']*=n['width']/length*.96
s['provenance']['notes']+=' Source circular error photos retain reviewed elliptical clipping. Two physical simulation object illustrations cropped back to their source-visible regions. Paragraph word spacing and font metrics approximate source Aptos.'
f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
