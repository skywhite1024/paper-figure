"""Rebuild ELSIM Figure 1; remove duplicate Type3 text already present as glyph paths."""
import argparse,json,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args()
out=r/'data/diagrams/elsim';subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(r/'research/survey/elsim-config.json'),'--out',str(out)],check=True)
f=out/'elsim-figure-1.json';s=json.loads(f.read_text());s['nodes']=[n for n in s['nodes'] if n.get('source_font')!='Unnamed-T3'];s['provenance']['notes']+=' Type3 font text records removed because their original glyph outlines already exist as editable source paths.';f.write_text(json.dumps(s,indent=2))
subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/elsim'),'--preview','--force'],cwd=r,check=True)
