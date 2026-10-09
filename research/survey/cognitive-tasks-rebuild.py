slug='cognitive-tasks'
import argparse,json,sys,subprocess,fitz,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
p=argparse.ArgumentParser();p.add_argument('--pdf',required=True);a=p.parse_args();cfg=json.load(open(R/'research/survey'/f'{slug}-config.json'));out=R/'data/diagrams'/slug;s=extract(Path(a.pdf),cfg,out);page=fitz.open(a.pdf)[cfg['page']-1];crop=fitz.Rect(cfg['crop']);scale=cfg['scale'];backgrounds=[]
def panel(id,b,fill,stroke='#18323D',radius=6):
 r=fitz.Rect(b);w=r.width*scale;h=r.height*scale;rad=radius*scale
 n={'id':id,'shape':'path','x':(r.x0-crop.x0)*scale,'y':(r.y0-crop.y0)*scale,'width':w,'height':h,'fill':fill,'stroke':stroke,'stroke_width':1.2,'commands':[{'moveTo':{'x':rad,'y':0}},{'lineTo':{'x':w-rad,'y':0}},{'quadBezTo':{'x1':w,'y1':0,'x':w,'y':rad}},{'lineTo':{'x':w,'y':h-rad}},{'quadBezTo':{'x1':w,'y1':h,'x':w-rad,'y':h}},{'lineTo':{'x':rad,'y':h}},{'quadBezTo':{'x1':0,'y1':h,'x':0,'y':h-rad}},{'lineTo':{'x':0,'y':rad}},{'quadBezTo':{'x1':0,'y1':0,'x':rad,'y':0}},{'close':{}}]};backgrounds.append(n)

panel('agent-interaction-background',[82.9,153.4,292.2,238.1],'#E6EBF7','#BEC6D8',0)
panel('task-evolution-background',[292.2,152.9,460,238.1],'#FFF5D8','#CDC8B4',0)
s['nodes']=backgrounds+s['nodes'];s['provenance']['notes']+=' Two rectangular source bitmap background panels reconstructed natively; broad gradient shadows omitted. Source sensor/photo examples remain separate raster images.'

f=out/(cfg['id']+'.json');f.write_text(json.dumps(s,indent=2));subprocess.run([sys.executable,'-m','paper_figure','export',str(f),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
