"""Correct source font's broken Unicode map after visual comparison with original Fig2."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'data/diagrams/rgsd-figure-2/rgsd-figure-2.json';s=json.loads(p.read_text())
replacements={9:'ref',16:'t',20:'t',31:'t',44:'t',59:'t',66:'t',99:'a',102:'+',106:'−',109:'a',111:'+',113:'−',261:'t'}
for n in s['nodes']:
 if n.get('shape')!='text':continue
 seq=n.get('source_seqno')
 if seq in replacements:n['label']=replacements[seq]
 if 'TimesNewRoman' in n.get('source_font',''):n['font_family']='Times New Roman'
 if seq in [176,200]:n['width']+=2
# Rotated invisible character supplied by source generator is not a semantic label;
# the actual cosine diamond outlines are already native PDF paths.
s['nodes']=[n for n in s['nodes'] if not(n.get('shape')=='text' and n.get('source_seqno') in [251,257])]
s['provenance']['text_repairs']='Visually repaired source broken ToUnicode map: ref, t,a,+,− glyphs. Removed2 rotated d artifact glyphs; native cosine diamond outlines preserved. Times New Roman used for source Times labels.'
s['provenance']['raster_review']='Six discrete raster motion/environment/lock inserts visually verified; oversized environment image placements are clipped to visible photos. Source math/labels remain native. Neighboring path-box warnings inspected rather than blindly suppressed.'
p.write_text(json.dumps(s,indent=2,ensure_ascii=False))
