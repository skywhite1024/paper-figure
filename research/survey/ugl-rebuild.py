"""Rebuild UGL Figure 7 with the source Tinos serif font mapped to Times New Roman."""
import argparse,json,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args()
out=r/'data/diagrams/ugl';subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(r/'research/survey/ugl-config.json'),'--out',str(out)],check=True)
f=out/'ugl-figure-7.json';s=json.loads(f.read_text())
for n in s['nodes']:
 if n.get('source_font')=='Tinos':n['font_family']='Times New Roman'
f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/ugl'),'--preview','--force'],cwd=r,check=True)
