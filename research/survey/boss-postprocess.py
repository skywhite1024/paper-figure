"""Restore source heading knockout that crosses the figure crop boundary."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];p=r/'data/diagrams/boss-figure-1/boss-figure-1.json';s=json.loads(p.read_text())
i=next(i for i,n in enumerate(s['nodes']) if n['id']=='pdf-text-47-0');s['nodes'].insert(i,dict(id='execute-title-white-knockout',shape='rect',x=1013,y=0,width=126,height=60,fill='#FFFFFF',stroke='none',source_seqno=200))
s['provenance']['crop_repair']='Restored the native white heading backing behind Execute New Task, whose original backing crossed the top crop boundary; this prevents a container border from crossing live title text.'
p.write_text(json.dumps(s,indent=2))
