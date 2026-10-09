"""Recover typeable source CID font labels with reviewed bold/italic mapping."""
import argparse,json,subprocess,sys,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/foundation-survey';cfg=r/'research/survey/foundation-survey-config.json'
subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(cfg),'--out',str(out)],check=True);f=out/'foundation-survey-figure-2.json';s=json.loads(f.read_text());s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('source_seqno')==45)]
for n in s['nodes']:
 if n['shape']=='text' and n.get('source_font','').startswith('CIDFont'):
  n['font_family']='Arial';n['bold']=n['source_font'] in ['CIDFont+F1','CIDFont+F2'];n['italic']=n['source_font'] in ['CIDFont+F2','CIDFont+F4'];n['font_size']=min(n['font_size'],n['width']/max(.1,fitz.Font('hebo' if n['bold'] else 'helv').text_length(n['label'],fontsize=1)))
s['provenance']['notes']+=' CID F1/F2 bold and F2/F4 italic mapping restored from source flags; invisible clipped white Transition label45 removed. Ordinary labels remain live text.';f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/foundation-survey'),'--preview','--force'],cwd=r,check=True)
