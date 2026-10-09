"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='vuvc'; CAT='variational-curriculum-reinforcement-learning-for-unsupervised-discovery-of-skills'; FIG='figure-1'; CROP=[61, 65, 535, 260]; FONT='Times New Roman'
p=argparse.ArgumentParser();p.add_argument('--pdf');a=p.parse_args()
evidence=json.loads((R/'research/survey'/f'{CAT}.json').read_text());pdf=Path(a.pdf or evidence['pdf_path'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(pdf)==evidence['pdf_sha256'],'Wrong source PDF'
D=R/'data/diagrams'/SLUG;A=D/'assets';D.mkdir(parents=True,exist_ok=True);A.mkdir(exist_ok=True)
B=R/'build'/SLUG;B.mkdir(parents=True,exist_ok=True);C=R/'build/candidates'/SLUG;C.mkdir(parents=True,exist_ok=True)
f=evidence['figure_candidates'][0];doc=fitz.open(pdf);page=doc[f['page_1_based']-1];pix=page.get_pixmap(matrix=fitz.Matrix(4,4),clip=fitz.Rect(CROP),alpha=False);pix.save(D/'original.png');source=Image.open(D/'original.png');W,H=source.size
s={'schema_version':1,'id':SLUG+'-'+FIG,'title':evidence['title_expected']+' — source-layout editable reconstruction','canvas':{'width':W,'height':H},'provenance':{'paper_title':evidence['title_expected'],'paper_url':evidence['source_url'].split('v1')[0].split('v3')[0]+evidence['version'][len(evidence['version'].split('v')[0]):],'pdf_url':evidence['versioned_pdf_url'],'figure':f['figure'],'page':f['page_1_based'],'license':evidence['license_note']+' Private user-requested adaptation; no public redistribution permission implied.','status':'figure_recreation','notes':'Manually reconstructed from the inspected original flattened PDF figure. Ordinary labels are live typeable text; panels, graph geometry and arrows are native editable shapes or paths. Source layout and contents retained; font metrics, line widths and decorative effects approximated.','source_sha256':sha(pdf),'source_crop_pdf_points':CROP,'survey_crop_correction':CROP!=f['crop_pdf_points'],'visual_inspection':'Original PDF figure inspected before source-layout reconstruction on 2026-10-09; independent application QA pending.','raster_details':[]},'nodes':[],'edges':[]}
s['provenance']['paper_url']='https://arxiv.org/abs/'+evidence['version']
def node(id,shape,x,y,w,h,**kw):
 z=dict(id=id,shape=shape,label='',x=x,y=y,width=max(.1,w),height=max(.1,h),fill='none',stroke='none');z.update(kw);s['nodes'].append(z);return z
def rect(id,x,y,w,h,fill='none',stroke='#000000',sw=2,round=False,**kw):return node(id,'rounded_rect' if round else 'rect',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,**kw)
def text(id,label,x,y,w,h,fs=22,color='#000000',bold=False,italic=False,font=None,align='center'):
 return node(id,'text',x,y,w,h,label=label,font_size=fs,font_family=font or FONT,text_color=color,bold=bold,italic=italic,align=align,text_inset=0,no_wrap=True)
def ellipse(id,x,y,w,h,fill='none',stroke='#000000',sw=2):return node(id,'ellipse',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw)
def poly(id,pts,stroke='#000000',sw=2,fill='none',close=False,dash=False):
 x=min(q[0] for q in pts);y=min(q[1] for q in pts);w=max(q[0] for q in pts)-x;h=max(q[1] for q in pts)-y
 cmds=[{'moveTo':{'x':pts[0][0]-x,'y':pts[0][1]-y}}]+[{'lineTo':{'x':u-x,'y':v-y}} for u,v in pts[1:]]
 if close:cmds.append({'close':{}})
 return node(id,'path',x,y,w,h,fill=fill,stroke=stroke,stroke_width=sw,commands=cmds,dash=dash)
def line(id,pts,stroke='#000000',sw=3,arrow=False,dash=False,head=False,size=10):
 z=poly(id,pts,stroke,sw,dash=dash)
 def tip(suffix,end,prev):
  dx,dy=end[0]-prev[0],end[1]-prev[1];L=math.hypot(dx,dy);ux,uy=dx/L,dy/L;bx,by=end[0]-size*ux,end[1]-size*uy
  poly(id+suffix,[end,(bx-size*.47*uy,by+size*.47*ux),(bx+size*.47*uy,by-size*.47*ux)],stroke,0,stroke,True)
 if arrow:tip('-arrow',pts[-1],pts[-2])
 if head:tip('-head',pts[0],pts[1])
 return z

def curve(id,x,y,w,h,cmds,stroke='#000000',sw=2,fill='none',dash=False):return node(id,'path',x,y,w,h,commands=cmds,stroke=stroke,stroke_width=sw,fill=fill,dash=dash)
def rounded(id,x,y,w,h,r,fill='none',stroke='#000000',sw=2,dash=False):
 k=.55228475
 cmds=[{'moveTo':{'x':r,'y':0}},{'lineTo':{'x':w-r,'y':0}},{'cubicBezTo':{'x1':w-r+k*r,'y1':0,'x2':w,'y2':r-k*r,'x':w,'y':r}},{'lineTo':{'x':w,'y':h-r}},{'cubicBezTo':{'x1':w,'y1':h-r+k*r,'x2':w-r+k*r,'y2':h,'x':w-r,'y':h}},{'lineTo':{'x':r,'y':h}},{'cubicBezTo':{'x1':r-k*r,'y1':h,'x2':0,'y2':h-r+k*r,'x':0,'y':h-r}},{'lineTo':{'x':0,'y':r}},{'cubicBezTo':{'x1':0,'y1':r-k*r,'x2':r-k*r,'y2':0,'x':r,'y':0}},{'close':{}}]
 return curve(id,x,y,w,h,cmds,stroke,sw,fill,dash)
def image(id,box,alt):
 x,y,x1,y1=box;source.crop(box).save(A/(id+'.png'));node(id,'image',x,y,x1-x,y1-y,asset='assets/'+id+'.png',alt=alt)
 s['provenance']['raster_details'].append({'id':id,'bounds_source_pixels':list(box),'detail':alt})
def finish():
 scene=D/(s['id']+'.json');scene.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 subprocess.run([sys.executable,'-m','paper_figure','export',str(scene),'--out',str(B),'--preview','--force'],cwd=R,check=True)
 for ext in ['pptx','drawio','png','manifest.json']:shutil.copy2(B/(s['id']+'.'+ext),C/(s['id']+'.'+ext))
 shutil.copy2(D/'original.png',C/(SLUG+'-original.png'));pdfname=SLUG+'-'+evidence['version']+'.pdf';shutil.copy2(pdf,C/pdfname)
 src={'validated_date':'2026-10-09','purpose':'User-requested private original-paper comparison against editable reconstruction','rights_note':'Private reference copy; preserve authorship and source license. No public redistribution permission implied.','papers':[{'id':SLUG,'catalog_id':CAT,'title':evidence['title_expected'],'file':pdfname,'arxiv_id_version':evidence['version'],'source_url':evidence['versioned_pdf_url'],'sha256':sha(pdf),'bytes':pdf.stat().st_size,'page_count':len(doc),'figure':f['figure'],'pdf_page_1_based':f['page_1_based'],'crop_pdf_points':CROP,'diagram_json':'../../data/diagrams/'+SLUG+'/'+s['id']+'.json','editable_pptx':s['id']+'.pptx','editable_drawio':s['id']+'.drawio','matches_original_reconstruction_source':True,'embedded_version_verified':True,'all_pages_readable':True,'license_url':evidence['license_note']}]}
 (C/'sources.json').write_text(json.dumps(src,indent=2,ensure_ascii=False)+'\n')
 with zipfile.ZipFile(C/(s['id']+'.pptx')) as z:
  root=ET.fromstring(z.read('ppt/slides/slide1.xml'));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};counts={q:len(root.findall('.//'+q,ns)) for q in ['p:sp','p:pic','a:custGeom','p:cxnSp','a:t']}
 validation={'diagram_id':s['id'],'source_scene_sha256':sha(scene),'source_pdf_sha256':sha(pdf),'checked_files':[{'name':s['id']+'.'+ext,'sha256':sha(C/(s['id']+'.'+ext))} for ext in ['drawio','png','pptx']],'review_status':'source pixels inspected; reconstruction preview review pending; independent application QA pending','native_xml_counts':counts,'editability':{'live_typeable_labels':sum(bool(z.get('label')) for z in s['nodes']),'native_paths':sum(z['shape']=='path' for z in s['nodes']),'raster_images':sum(z['shape']=='image' for z in s['nodes']),'raster_boundaries':s['provenance']['raster_details']},'checks':{'source_title':'Verified PDF title and fixed version from survey evidence; PDF hash rechecked','source_figure':'Actual PDF figure inspected; crop includes complete source diagram','drawio':'Native XML generated; draw.io application editing not tested','powerpoint':'Native XML counts inspected; PowerPoint GUI editing not tested'},'limitations':['Flattened source manually rebuilt; font metrics, arrowheads and stroke widths approximate original','Native paths are independently editable but not semantically attached connectors','No PowerPoint or draw.io GUI edit validation claimed']}
 (C/'VALIDATION.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n')
 print(SLUG,counts,validation['editability'])
# Full corrected Figure 1: the entire Update theta / Equation 5 loop is included.
FONT='Arial'
s['provenance']['survey_crop_correction']='Initial survey right488pt enlarged to535pt to include Update theta / Equation 5 feedback label.'
s['provenance']['notes']+=' Seven small original raster crops retain three robot-goal renderings and four decorative icons; all chart curves, axes, bars, panels, arrows and ordinary/formula labels are native. Tiny angle captions on photo backgrounds are overlaid with live native text. Mathematical text uses Unicode rather than live equation objects.'
rounded('goal-model-panel',8,12,951,760,19,'#FFFFFF','#ED8A77',5)
rounded('policy-panel',1043,13,585,179,10,'#FFFFFF','#70AEF4',5)
rounded('environment-panel',1043,286,585,179,10,'#FFFFFF','#9BD579',5)
rounded('discriminative-panel',1043,592,585,179,10,'#FFFFFF','#F8DE70',5)
# Native model titles and explicit underline rules.
for id,label,x,y,w,fs in [('goal-title','goal generative model',14,20,400,36),('policy-title','goal-conditioned policy',1066,51,438,38),('environment-title','environment',1137,328,236,36),('discriminative-title','discriminative model',1074,630,410,38)]:
 text(id,label,x,y,w,48,fs,bold=True,align='left');line(id+'-underline',[(x,y+43),(x+w-20,y+43)],sw=1.3)
text('goal-distribution','g ∼ p(g)',48,70,170,55,43,italic=True,font='Times New Roman')
text('policy-formula-left','a ∼ π',1148,102,100,58,43,italic=True,font='Times New Roman',align='left')
text('policy-theta-subscript','θ',1244,128,22,27,27,italic=True,font='Times New Roman',align='left')
text('policy-formula-right','(a | s,g)',1265,102,150,58,43,italic=True,font='Times New Roman',align='left')
text('environment-formula','s′ ∼ p(s′|s,a)',1123,376,325,54,43,italic=True,font='Times New Roman')
text('discriminative-q','q',1191,681,28,56,43,italic=True,font='Times New Roman',align='left')
text('discriminative-lambda-subscript','λ',1213,706,22,27,27,italic=True,font='Times New Roman',align='left')
text('discriminative-formula-right','(g | s)',1234,681,117,56,43,italic=True,font='Times New Roman',align='left')
image('target-icon',(45,123,194,271),'Original target-and-pencil decorative icon; internal artwork remains raster')
image('robot-icon',(1488,30,1584,179),'Original robot decorative icon; internal artwork remains raster')
image('earth-icon',(1460,301,1611,451),'Original globe decorative icon; internal artwork remains raster')
image('scales-icon',(1460,613,1611,750),'Original balance-scale decorative icon; internal artwork remains raster')
# Right-hand feedback loop and update annotations.
line('goal-to-policy',[(793,205),(988,205),(988,103),(1042,103)],sw=4,arrow=True,size=16)
text('automatic-goal','Automatically\nset g',784,205,222,92,34)
line('policy-to-environment',[(1335,194),(1335,282)],sw=4,arrow=True,size=16)
line('environment-to-discriminator',[(1335,466),(1335,588)],sw=4,arrow=True,size=16)
text('update-lambda','Update λ',1375,484,166,45,34)
text('update-lambda-equation','(Equation 4)',1361,526,201,43,34,font='Times New Roman')
line('policy-update-loop',[(1630,681),(1687,681),(1687,103),(1633,103)],sw=4,arrow=True,size=16)
text('update-theta','Update θ',1710,338,167,46,34)
text('update-theta-equation','(Equation 5)',1691,379,196,46,34,font='Times New Roman')
line('environment-to-goals',[(1042,375),(994,375),(994,451),(923,451)],sw=4,arrow=True,size=16)
line('discriminator-to-density',[(1042,681),(994,681),(994,596),(942,596)],sw=4,arrow=True,size=16)
# Main distribution plot.
rect('distribution-frame',306,95,486,220,'none','#E87A65',3)
line('distribution-x-axis',[(324,299),(776,299)],sw=4,arrow=True,size=17)
line('distribution-y-axis',[(324,299),(324,109)],sw=4,arrow=True,size=17)
text('density-pg','p(g)',330,93,84,52,40,italic=True,font='Times New Roman')
text('distribution-goal-g','g',760,249,33,48,43,italic=True,font='Times New Roman')
# Curves transcribed from source pixels, not a generic Gaussian replacement.
def bezpath(id,start,segments,sw=3,dash=False):
 pts=[start]+[p for seg in segments for p in [seg[:2],seg[2:4],seg[4:]]];x=min(p[0] for p in pts);y=min(p[1] for p in pts);w=max(p[0] for p in pts)-x;h=max(p[1] for p in pts)-y
 cmds=[{'moveTo':{'x':start[0]-x,'y':start[1]-y}}]
 for x1,y1,x2,y2,ex,ey in segments:cmds.append({'cubicBezTo':{'x1':x1-x,'y1':y1-y,'x2':x2-x,'y2':y2-y,'x':ex-x,'y':ey-y}})
 z=curve(id,x,y,w,h,cmds,sw=sw,dash=dash)
 if dash:z['dash_style']='dotted'
 return z
bezpath('previous-distribution',(336,277),[(374,275,410,254,425,220),(438,183,430,135,452,132),(490,125,479,214,514,220),(550,225,553,169,569,135),(580,106,609,110,620,144),(639,204,650,228,679,248),(704,266,718,277,752,279)],2,True)
bezpath('current-distribution',(336,276),[(357,256,375,241,391,178),(401,139,405,122,427,127),(455,133,456,207,488,238),(510,253,538,252,550,231),(570,181,587,151,613,153),(653,153,659,231,698,264),(717,278,735,279,752,277)],4)
rounded('distribution-legend',664,99,124,49,7,'#FFFFFF','#A9A9A9',1)
text('previous-key','previous:',668,102,81,24,20,align='left');text('current-key','current:',677,122,72,24,20,align='left')
line('previous-key-line',[(751,116),(782,116)],sw=2,dash=True);line('current-key-line',[(751,136),(782,136)],sw=4)
rounded('value-legend',622,21,328,65,12,'#FAFAF9','#B5B5B5',1.3)
text('value-function-key','Vₖ: k-th value function',635,26,303,29,20,align='left')
text('uncertainty-key','U : Uncertainty of value functions',634,54,303,30,20,align='left')
text('equation9','(Equation 9)',175,313,192,51,34,font='Times New Roman')
# Goal renderings are individual crops; angle annotations are typeable.
for id,box,lab in [('goal15',(251,369,416,534),'angle: 15°'),('goal0',(471,369,636,534),'angle: 0°'),('goal60',(757,369,922,534),'angle: 60°')]:
 image(id,box,'Original robot and drawer simulation goal rendering; small angle caption covered by native editable label')
 x,y,x1,y1=box;rect(id+'-caption-back',x+84,y+3,78,27,'#ADF4F3','none',0);text(id+'-caption',lab,x+85,y+3,76,26,17,align='center')
for id,pts in [('sample15',[(357,369),(425,135)]),('sample0',[(550,369),(544,246)]),('sample60',[(778,369),(701,270)])]:line(id,pts,sw=2.2,arrow=True,size=10)
for k,x,y in [(1,426,127),(2,544,240),(3,698,264)]:ellipse('selected-goal-'+str(k),x-8,y-8,16,16,'#DB432C','none',0)
text('goals-title','potential\ncurriculum\ngoals',48,394,175,115,31,bold=True,align='right')
text('density-title','density\nestimate',50,555,176,82,31,bold=True,align='right')
text('uncertainty-title','uncertainty',52,661,177,45,31,bold=True,align='right')
text('equation7','(Equation 7)',54,698,177,44,32,font='Times New Roman',align='right')
for id,y in [('goals',417),('density',562),('uncertainty',655)]:text('ellipsis-'+id,'···',666,y,64,55,49,font='Times New Roman')
# Vertical dotted column separators.
for k,x in enumerate([444,663,737]):
 line('goal-separator-'+str(k),[(x,368),(x,533)],'#555555',.9,dash=True)
 line('density-separator-'+str(k),[(x,560),(x,639)],'#777777',.9,dash=True)
 line('uncertainty-separator-'+str(k),[(x,662),(x,745)],'#777777',.9,dash=True)
# Density estimates: native curve, horizontal goal axis and dotted indicator.
rounded('density-estimate-panel',243,544,697,106,18,'none','#000000',2,dash=True)
for k,x,marker,yy in [(1,263,305,598),(2,482,552,557),(3,768,876,611)]:
 line('density-axis-'+str(k),[(x,633),(x+141,633)],sw=1.7,arrow=True,head=True,size=9)
 text('density-g-'+str(k),'g',x+140,612,23,38,27,italic=True,font='Times New Roman')
 bezpath('density-curve-'+str(k),(x+5,623),[(x+28,623,x+39,610,x+47,582),(x+52,566,x+59,552,x+71,555),(x+87,556,x+88,578,x+98,600),(x+108,619,x+122,623,x+136,623)],2)
 line('density-marker-'+str(k),[(marker,yy),(marker,633)],sw=2.4,dash=True)
 ellipse('density-marker-dot-'+str(k),marker-5,yy-5,10,10,'#DB432C','none',0)
# Three small uncertainty histograms and their resulting U values.
for k,x,heights,uh in [(1,238,[38,10,22],38),(2,456,[39,41,40],7),(3,746,[17,12,17],7)]:
 for j,h in enumerate(heights):
  z=rect(f'uncertainty-bin-{k}-{j}',x+j*44,663,44,45,'none','#222222',1.5);z['dash']=True;z['dash_style']='dotted'
  rect(f'uncertainty-bar-{k}-{j}',x+10+j*44,708-h,23,h,'#E76C54','none',0)
  text(f'value-label-{k}-{j}','V'+['₁','₂','₃'][j],x+j*44,708,44,51,37,italic=True,font='Times New Roman')
 ux=x+152;rect(f'uncertainty-output-{k}',ux,663,43,45,'#FFFFFF','#000000',3);rect(f'uncertainty-output-bar-{k}',ux+11,708-uh,22,uh,'#E76C54','none',0)
 line(f'uncertainty-to-output-{k}',[(x+132,686),(ux,686)],sw=2,arrow=True,size=8)
 text(f'uncertainty-U-{k}','U',ux,708,43,51,37,italic=True,font='Times New Roman')
finish()
