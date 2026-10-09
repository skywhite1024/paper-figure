"""Rebuild SLAC with clipped photo subassets and editable glyph outlines for rotated labels only."""
import argparse,json,subprocess,sys,re,tempfile,fitz,copy
from pathlib import Path
from lxml import etree
r=Path(__file__).resolve().parents[2];sys.path.insert(0,str(r));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/slac';cfg=json.loads((r/'research/survey/slac-config.json').read_text());s=extract(Path(a.pdf),cfg,out);page=fitz.open(a.pdf)[cfg['page']-1];spans=[v for v in page.get_texttrace() if tuple(v.get('dir',(1,0)))!=(1,0) and fitz.Rect(cfg['crop']).intersects(fitz.Rect(v['bbox']))];seqs={v['seqno'] for v in spans};positions=[c[2] for v in spans if v['seqno']==92 for c in v['chars']];svg=etree.fromstring(page.get_svg_image(text_as_path=True).encode())
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
# Source words Task, Policy and Filter are native typeable 90-degree text, not glyph paths.
for seq,label in [(152,'Task'),(154,'Policy'),(205,'Filter')]:
 v=next(z for z in spans if z['seqno']==seq);box=fitz.Rect(v['bbox']);scale=cfg['scale'];cx=(box.x0+box.x1-2*cfg['crop'][0])*scale/2;cy=(box.y0+box.y1-2*cfg['crop'][1])*scale/2;w=box.height*scale;h=box.width*scale
 s['nodes'].append({'id':f'slac-rotated-live-{seq}','shape':'text','label':label,'x':cx-w/2,'y':cy-h/2,'width':w,'height':h,'font_size':v['size']*scale,'font_family':'Arial','text_color':'#000000','align':'center','text_inset':0,'no_wrap':True,'rotation':90})
fixed=[]
for n in s['nodes']:
 if n['id']=='pdf-path-4':continue
 if n['id'] in [f'pdf-path-{i}' for i in [17,71,72,73,176,196,214]]:
  parts=[]
  for command in n['commands']:
   if 'moveTo' in command:parts.append([])
   parts[-1].append(command)
  for j,part in enumerate(parts):
   nn=copy.deepcopy(n);nn['id']+=f'-part-{j}';nn['commands']=part;fixed.append(nn)
 else:fixed.append(n)
pts=[(0,.795),(4.28,.795),(4.28,0),(6.67,1.196),(4.28,2.39),(4.28,1.59),(0,1.59)];scale=cfg['scale'];cx,cy=cfg['crop'][:2]
fixed.append({'id':'slac-empowerment-green-arrow','shape':'path','x':(222.1-cx)*scale,'y':(107.62-cy)*scale,'width':6.67*scale,'height':2.39*scale,'fill':'#4EA72E','stroke':'none','commands':[{'moveTo':{'x':pts[0][0]*scale,'y':pts[0][1]*scale}}]+[{'lineTo':{'x':x*scale,'y':y*scale}} for x,y in pts[1:]]+[{'close':{}}]})
s['nodes']=fixed
s['provenance']['notes']+=' Task, Policy and Filter are live90degree text; only the slanted mathematical ellipsis is a glyph outline. Other ordinary text remains typeable. Broad shadow images omitted, panel shadows simplified.';s['provenance']['rotated_text_source_seqnos']=sorted(seqs);f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/slac'),'--preview','--force'],cwd=r,check=True)
