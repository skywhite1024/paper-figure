"""Rebuild SLAC with clipped photo subassets and editable glyph outlines for rotated labels only."""
import argparse,json,subprocess,sys,re,tempfile,fitz
from pathlib import Path
from lxml import etree
r=Path(__file__).resolve().parents[2];sys.path.insert(0,str(r));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/slac';cfg=json.loads((r/'research/survey/slac-config.json').read_text());s=extract(Path(a.pdf),cfg,out);page=fitz.open(a.pdf)[cfg['page']-1];spans=[v for v in page.get_texttrace() if tuple(v.get('dir',(1,0)))!=(1,0) and fitz.Rect(cfg['crop']).intersects(fitz.Rect(v['bbox']))];seqs={v['seqno'] for v in spans};positions=[c[2] for v in spans for c in v['chars']];svg=etree.fromstring(page.get_svg_image(text_as_path=True).encode())
for e in list(svg.iter()):
 if e is svg or any(a.tag.rsplit('}',1)[-1]=='defs' for a in e.iterancestors()):continue
 tag=e.tag.rsplit('}',1)[-1]
 if tag in ('svg','defs','g'):continue
 keep=False
 if tag=='use' and e.get('data-text') is not None:
  vs=re.findall(r'[-+]?(?:[0-9]*\.)?[0-9]+(?:[eE][-+]?[0-9]+)?',e.get('transform',''))
  if len(vs)==6:
   x,y=map(float,vs[-2:]);keep=any(abs(x-p[0])+abs(y-p[1])<.08 for p in positions)
 if not keep and e.getparent() is not None:e.getparent().remove(e)
with tempfile.TemporaryDirectory(prefix='slac-labels-') as tmp:
 tmp=Path(tmp);v=fitz.open(stream=etree.tostring(svg),filetype='svg');(tmp/'glyphs.pdf').write_bytes(v.convert_to_pdf());gc={**cfg,'id':'slac-rotated-labels','page':1,'outline_fonts':[],'reviewed_raw_images':[],'raster_regions':[]};g=extract(tmp/'glyphs.pdf',gc,tmp/'glyphs');s['nodes']=[n for n in s['nodes'] if not(n['shape']=='text' and n.get('source_seqno') in seqs)]
 for n in g['nodes']:
  n['id']='slac-rotated-'+n['id'];s['nodes'].append(n)
s['provenance']['notes']+=' Only six rotated source spans are editable glyph outlines; all other source text remains typeable. Broad shadow images omitted, panel shadows simplified.';s['provenance']['rotated_text_source_seqnos']=sorted(seqs);f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/slac'),'--preview','--force'],cwd=r,check=True)
