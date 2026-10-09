"""Restore reviewed source clipping outlines as native geometry for survey Figure1."""
import argparse,json,subprocess,sys,fitz
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();out=r/'data/diagrams/temporal-survey';cfg=json.loads((r/'research/survey/temporal-survey-config.json').read_text());subprocess.run([sys.executable,str(r/'research/extract_pdf_figure.py'),'--pdf',a.pdf,'--config',str(r/'research/survey/temporal-survey-config.json'),'--out',str(out)],check=True)
f=out/(cfg['id']+'.json');s=json.loads(f.read_text());nodes={n.get('source_seqno'):n for n in s['nodes'] if n['shape']=='path'};page=fitz.open(a.pdf)[cfg['page']-1];ext=page.get_drawings(extended=True);scale=cfg['scale'];crop=fitz.Rect(cfg['crop']);repaired=[]
for j,d in enumerate(ext):
 if 'seqno' not in d or d['seqno'] not in nodes or j==0:continue
 clip=next((q for q in reversed(ext[:j]) if q.get('type')=='clip' and q.get('level')==d.get('level',0)-1), {})
 if clip.get('type')!='clip' or clip['level']+1!=d.get('level'):continue
 box=fitz.Rect(clip['scissor']);node=nodes[d['seqno']]
 if d['type'] in ('s','fs') and sum(abs(x-y) for x,y in zip(box,d['rect']))<.05:
  node['stroke_width']/=2;repaired.append([d['seqno'],'inside-clipped stroke halved']);continue
 if d['type']!='f' or len(d['items'])!=1 or d['items'][0][0]!='re' or not fitz.Rect(d['rect']).contains(box) or not crop.contains(box):continue
 if any(item[0] not in ('l','c') for item in clip['items']):continue
 if box.width*scale<.01 or box.height*scale<.01:continue
 commands=[];last=None
 def pt(v):return {'x':(v.x-box.x0)*scale,'y':(v.y-box.y0)*scale}
 for item in clip['items']:
  k=item[0]
  if k not in ('l','c'):raise ValueError('Unreviewed clipping operation '+k)
  start=item[1]
  if last is None or abs(last.x-start.x)+abs(last.y-start.y)>.0001:commands.append({'moveTo':pt(start)})
  if k=='l':commands.append({'lineTo':pt(item[2])});last=item[2]
  else:
   b,c,e=item[2:];commands.append({'cubicBezTo':{'x1':(b.x-box.x0)*scale,'y1':(b.y-box.y0)*scale,'x2':(c.x-box.x0)*scale,'y2':(c.y-box.y0)*scale,**pt(e)}});last=e
 commands.append({'close':{}});node.update(commands=commands,x=(box.x0-crop.x0)*scale,y=(box.y0-crop.y0)*scale,width=box.width*scale,height=box.height*scale);repaired.append([d['seqno'],'clip outline restored'])
s['provenance']['reviewed_clip_repairs']=repaired;s['provenance']['notes']+=' Native arrow shapes recovered from original source clipping outlines; inside-clipped border strokes use half source width.';f.write_text(json.dumps(s,indent=2));print(repaired)
subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(r/'build/temporal-survey'),'--preview','--force'],cwd=r,check=True)
