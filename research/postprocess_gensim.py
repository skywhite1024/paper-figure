"""Native transcription of source raster LLM/code labels; run after extraction."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/diagrams/gensim/gensim-figure-2.json';d=json.loads(p.read_text())
def text(id,label,x,y,w,h,size=3.3,font='Courier New',color='#333333',bold=False):
 d['nodes'].append(dict(id=id,shape='text',label=label,x=(x-107)*4,y=(y-62)*4,width=w*4,height=h*4,font_size=size*4,font_family=font,text_color=color,bold=bold,align='left',no_wrap=True,text_inset=0))
for i,label in enumerate(['Large','Language','Model']):
 text('llm-initial-'+str(i),label[0],168,104+i*9,7,9,7.4,'Arial','#0055BB',True)
 text('llm-rest-'+str(i),label[1:],168+(6.2 if i==2 else 4.5),104+i*9,36,9,7.4,'Arial','#111111',True)
lines=[('class BuildCar(Task):',205,71),('    """Construct a simple car structure using blocks and cylinders."""',205,77),('# Add wheels.',214,93),('wheel_size = (0.02, 0.02, 0.02)',214,99),('wheel_urdf = \'cylinder/cylinder-template.urdf\'',214,105),('self.add_goal(',245,125),('  objs=wheels,',245,131),('  matches=np.ones((4, 4)),',245,137),('...',245,143),('  language_goal="For the wheels,',245,149),('  place a black cylinder on each',245,155),('  side of the base blocks.")',245,161)]
for i,(label,x,y) in enumerate(lines):text('code-'+str(i),label,x,y,110 if i else 65,5,3.25,color='#294E82' if i in [0,1,9,10,11] else '#333333')
d['provenance']['manual_text_notes']='Source raster code and LLM words transcribed to native typeable text. Syntax highlighting simplified to whole-line colors for reliable editor spacing.'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
