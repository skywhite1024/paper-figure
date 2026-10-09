"""Restore inspected ordinary CompILE labels as typeable text, retaining math paths."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'data/diagrams/compile/compile-figure-2.json'
s=json.loads(p.read_text())
labels={37:'Step 1) Process input sequence',42:'Encoder',109:'Step 2) Process masked remainder',185:'Soft segment mask',276:'Input sequence x',278:'Loss, masked with soft',279:'segment mask (from encoder)',343:'Reconstruction',394:'Latent segment',395:'encoding',416:'Encoder',417:'Decoder',418:'Decoder',291:'Loss'}
for n in s['nodes']:
    number=n.get('source_seqno')
    if n['shape']=='path' and number in labels:
        n.update(shape='text',label=labels[number],font_family='Arial',font_size=16.79,text_color=n['fill'],
                 fill='none',stroke='none',text_inset=0,no_wrap=True,align='left',y=max(0,n['y']-2),height=21,width=n['width']+8)
        n.pop('commands',None)
s['provenance']['notes']+=' Fourteen ordinary outlined source labels were transcribed and restored as native typeable text; mathematical notation and vertical title glyphs retain source outlines. Small font-metric differences are expected.'
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
