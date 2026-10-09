"""Restore SkillWrapper source paths and ordinary text with individually bounded source photos."""
import json,sys,subprocess,math
from pathlib import Path
import fitz
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from paper_figure.pdf_extract import extract
from paper_figure.model import validate
slug='skillwrapper';papers=json.load(open(R/'data/catalog.json'))['papers'];m=json.load(open(R/'research/survey'/(papers[117]['id']+'.json')));f=m['figure_candidates'][0];pdf=R/m['pdf_path'];page=fitz.open(pdf)[f['page_1_based']-1];crop=fitz.Rect(f['crop_pdf_points']);regions=[]
for b in page.get_text('dict')['blocks']:
 if b['type']!=1:continue
 r=fitz.Rect(b['bbox'])
 if not crop.contains(r):continue
 found=False
 for a in regions:
  q=fitz.Rect(a['bbox'])
  if (q&r).get_area()>.95*min(q.get_area(),r.get_area()):a['bbox']=list(q|r);found=True;break
 if not found:regions.append({'bbox':list(r),'reason':'Individual original robot/environment photograph or icon; internal pixels remain raster'})
c={'id':slug+'-figure-1','paper_title':m['title_expected'],'paper_url':m['source_url'],'figure':'Figure 1','page':2,'crop':list(crop),'scale':3,'license':m.get('license_note','unverified'),'notes':'Original SkillWrapper data collection, predicate invention, operator learning and planning arrangement. Native geometry and live ordinary labels/code; mathematical glyphs retain native outlines. Original task photos/icons are individually bounded raster inserts.','outline_fonts':['CMM','CMSY','CMEX','CambriaMath'],'raster_regions':regions};(R/'research/configs/skillwrapper.json').write_text(json.dumps(c,indent=2));D=R/'data/diagrams'/slug;s=extract(pdf,c,D)
# Source bold lettering is fill-text plus separately stroked character outlines.
# Keep coherent live text only; duplicate stroke contours would remain after edits.
spans=page.get_texttrace();glyph_strokes=set()
for drawing in page.get_drawings():
 if drawing['type']!='s':continue
 for span in spans:
  if drawing['seqno']!=span['seqno']+1:continue
  r=fitz.Rect(span['bbox']);r.x0-=.35;r.x1+=.35;r.y0-=.35;r.y1+=.35
  if r.contains(drawing['rect']):glyph_strokes.add(drawing['seqno']);break
s['nodes']=[n for n in s['nodes']if not(n['shape']=='path'and n.get('source_seqno')in glyph_strokes)]
merged=[]
for n in s['nodes']:
 if n['shape']=='text' and merged:
  prev=merged[-1]
  if prev['shape']=='text'and prev.get('source_font')==n.get('source_font')and prev.get('text_color')==n.get('text_color')and abs(prev['y']-n['y'])<.25 and abs(prev['font_size']-n['font_size'])<.1 and n['source_seqno']-prev['source_seqno']<4:
   gap=n['x']-(prev['x']+prev['width'])
   if -.1<=gap<prev['font_size']*.65:
    prev['label']+=(' 'if gap>prev['font_size']*.15 and not prev['label'].endswith(' ') else '')+n['label'];prev['width']=n['x']+n['width']-prev['x'];prev['source_seqno']=n['source_seqno'];continue
 merged.append(n)
s['nodes']=merged
s['provenance']['ordinary_label_repair']='Source duplicate stroked character outlines removed; ordinary text character spans merged into coherent live labels/code lines.'
for n in s['nodes']:
 if n['shape']=='text':
  n['label']=n['label'].replace('ﬁ','fi').replace('ﬂ','fl');n['italic']=n.get('italic',False)or'Ital'in n.get('source_font','');n['bold']=n.get('bold',False)or any(t in n.get('source_font','')for t in ['Heavy','Black']);font=('tibo'if n.get('bold')else'tiro')if n.get('font_family')=='Times New Roman'else'hebo'if n.get('bold')else'helv';old=n['font_size'];n['font_size']*=min(1,n['width']/max(fitz.get_text_length(n['label'],fontname=font,fontsize=old),.01));n['y']=max(0,n['y']-.15*old+.5*(old-n['font_size']))
validate(s,D);scene=D/(s['id']+'.json');scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(R/'build'/slug),'--preview','--force'],cwd=R,check=True)
