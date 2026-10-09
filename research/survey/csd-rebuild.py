"""CSD Figure 2: split five reviewed overlapping stroke/endpoint compounds for Office parity."""
import argparse,json,subprocess,sys,copy
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/csd'
subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(r/'research/survey/csd-config.json'),'--out',str(out)],check=True)
f=out/'csd-figure-2.json';s=json.loads(f.read_text());nodes=[]
for n in s['nodes']:
 if n['id'] not in ['pdf-path-35','pdf-path-81','pdf-path-82','pdf-path-85','pdf-path-86']:nodes.append(n);continue
 segments=[]
 for c in n['commands']:
  if 'moveTo'in c:segments.append([])
  segments[-1].append(c)
 for j,seg in enumerate(segments):
  nn=copy.deepcopy(n);nn['id']+=f'-part-{j}';nn['commands']=seg;nodes.append(nn)
s['nodes']=nodes;s['provenance']['notes']+=' Five reviewed filled line/endpoint compound paths split into independent native subpaths to preserve solid endpoints under Office even-odd fill.';f.write_text(json.dumps(s,indent=2))
subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/csd'),'--preview','--force'],cwd=r,check=True)
