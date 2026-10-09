import argparse,json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();slug='affordance-worlds';cfg=json.load(open(R/'research/survey'/f'{slug}-config.json'));out=R/'data/diagrams'/slug;s=extract(Path(a.pdf),cfg,out);f=out/(cfg['id']+'.json');subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
