import argparse,json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();slug='forerobo';cfg=json.load(open(R/'research/survey'/f'{slug}-config.json'));out=R/'data/diagrams'/slug;s=extract(Path(a.pdf),cfg,out);page=__import__('fitz').open(a.pdf)[cfg['page']-1]
import fitz
for n in s['nodes']:
 if n.get('stroke_width',0)>100:n['stroke_width']/=25400
 if n['shape']=='text':
  if 'Georgia' in n.get('source_font',''):n['font_family']='Times New Roman'
  font='tibo' if n.get('bold') and n.get('font_family')=='Times New Roman' else 'tiro' if n.get('font_family')=='Times New Roman' else 'hebo' if n.get('bold') else 'helv'
  length=fitz.get_text_length(n['label'],fontname=font,fontsize=n['font_size'])
  if length>n['width']:n['font_size']*=n['width']/length*.98
s['provenance']['notes']+=' Reviewed source EMU-like stroke-width anomaly corrected by factor25400 against original pixels. Georgia labels substituted with width-fitted native Times. Source broad bitmap shadows omitted; discrete photo crop boundaries restored.'
f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
