"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='deep-sr'; CAT='eigenoption-discovery-through-the-deep-successor-representation'; FIG='figure-2'; CROP=[108, 80, 505, 180]; FONT='Times New Roman'
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
# Full Figure 2 includes lower SR estimator branch, omitted by the initial survey crop.
s['provenance']['survey_crop_correction']='Initial survey bottom173pt enlarged to180pt to include SR estimator dimensions.'
s['provenance']['notes']+=' All content, including the convolution blocks, dimensions and mathematical symbols, is native; no raster assets are embedded. Three-dimensional network tensors are editable face polygons.'
def cube(id,x,y,w,h,dx,dy):
 poly(id+'-top',[(x,y),(x+dx,y-dy),(x+w+dx,y-dy),(x+w,y)],'#333333',2.5,'#FFFFFF',True)
 side_x=x+w if dx>0 else x
 poly(id+'-side',[(side_x,y),(side_x+dx,y-dy),(side_x+dx,y+h-dy),(side_x,y+h)],'#333333',2.5,'#D7D7D7',True)
 rect(id+'-front',x,y,w,h,'#FFFFFF','#333333',2.5)
def patch(id,x,y,w,h,dx,dy):
 poly(id+'-top',[(x,y),(x+dx,y-dy),(x+w+dx,y-dy),(x+w,y)],'#777777',1.8,'none',True)
 side_x=x+w if dx>0 else x
 poly(id+'-side',[(side_x,y),(side_x+dx,y-dy),(side_x+dx,y+h-dy),(side_x,y+h)],'#777777',1.8,'none',True)
 rect(id+'-front',x,y,w,h,'none','#777777',1.8)
cube('input',29,96,35,103,36,36);patch('input-patch',49,106,36,20,11,11)
cube('conv1',187,114,40,77,31,30);patch('conv1-patch1',198,115,43,22,10,10);patch('conv1-patch2',198,151,41,9,10,10)
cube('conv2',344,122,39,60,26,23);patch('conv2-patch1',355,126,36,20,10,10);patch('conv2-patch2',355,154,35,8,10,10)
cube('conv3',499,136,28,40,18,18);patch('conv3-patch1',507,138,27,12,6,6);patch('conv3-patch2',507,157,27,7,6,6)
for id,x,y,w,h in [('representation1024',633,92,21,99),('representation2048',710,92,21,99),('reconstruction2048',842,91,21,100),('reconstruction1024',924,92,21,99),('sr2048',842,260,21,101),('sr1024',924,262,21,99),('sr2048out',1007,262,21,99)]:rect(id,x,y,w,h,'#FFFFFF','#333333',2.5)
cube('deconv1',1057,130,28,42,-16,16);patch('deconv1-patch1',1057,130,25,14,-9,8);patch('deconv1-patch2',1057,155,25,7,-9,7)
cube('deconv2',1201,121,40,59,-27,24);patch('deconv2-patch1',1203,122,30,20,-11,10);patch('deconv2-patch2',1203,148,30,11,-11,10)
cube('deconv3',1369,110,38,77,-33,29);patch('deconv3-patch1',1370,111,26,23,-13,11);patch('deconv3-patch2',1370,148,26,10,-13,10)
poly('output-face',[(1508,59),(1550,101),(1550,199),(1508,156)],'#333333',2.5,'#EEEEEE',True)
poly('output-side',[(1508,59),(1515,59),(1558,101),(1558,199),(1550,199),(1550,101)],'#333333',2.5,'#FFFFFF',True)
poly('output-patch',[(1514,91),(1528,104),(1528,124),(1514,110)],'#777777',1.8,'#D7D7D7',True)
# Native ordinary typeable labels and data dimensions.
for k,x,pad in [(1,112,0),(2,269,2),(3,422,2)]:
 text(f'conv-label-{k}',f'Conv\n64, 6x6\npad {pad}, {pad}\nstride 2',x,40,89,88,21,align='left')
for k,x,ch,pad in [(1,1095,64,2),(2,1256,64,2),(3,1425,1,0)]:
 text(f'deconv-label-{k}',f'Deconv\n{ch}, 6x6\npad {pad}, {pad}\nstride 2',x,39,87,88,21,align='left')
for k,x,lab,w in [('in',5,'4×84×84',112),('c1',157,'64×40×40',122),('c2',311,'64×20×20',131),('c3',459,'64×10×10',135),('fc1',610,'1024',66),('phi',688,'2048',66),('fc2',821,'2048',66),('fc3',903,'1024',65),('d1',1007,'64×10×10',135),('d2',1150,'64×20×20',147),('d3',1312,'64×40×40',145),('out',1481,'84×84',100)]:text('dimension-'+k,lab,x,203,w,28,23)
# Encoder and decoder progression.
for id,x1,x2,y,fc,relu in [('c1',111,178,141,False,True),('c2',269,336,141,False,True),('c3',424,490,141,False,True),('f1',555,623,141,True,True),('f2',662,701,141,True,False),('f3',872,914,141,True,False),('f4',955,1022,141,True,True),('d1',1096,1162,141,False,True),('d2',1257,1324,141,False,True),('d3',1425,1492,141,False,False)]:
 line('forward-'+id,[(x1,y),(x2,y)],'#444444',2.7,True,size=10)
 if fc:text('fc-'+id,'fc',x1,112,x2-x1,23,21)
 if relu:text('relu-'+id,'ReLU',x1,153,x2-x1,29,21)
text('phi','φ',685,45,42,49,40,italic=True)
rect('action-box',747,14,79,24,'#FFFFFF','#333333',2.5);text('action-label','action',750,14,73,24,23)
text('action-fc','fc',789,43,34,24,21)
line('action-to-fc',[(786,38),(786,64)],'#333333',2.5,True,size=9)
rect('action2048',735,64,102,21,'#FFFFFF','#333333',2.5);text('action-dimension','2048',745,64,82,22,21)
ellipse('elementwise-product',772,130,28,28,'#FFFFFF','#333333',2)
text('product-symbol','×',772,127,28,31,27)
line('action-to-product',[(786,85),(786,129)],'#333333',2.5,True,size=9)
line('phi-to-product',[(731,141),(772,141)],'#333333',2.5,True,size=9)
line('product-to-reconstruction',[(800,141),(840,141)],'#333333',2.5,True,size=9)
text('zeta','ζ',802,89,33,48,40,italic=True)
# Source bracket-like grouping rules and lower branch.
line('representation-bracket',[(6,231),(28,248),(724,248),(746,231)],'#444444',1.6)
text('representation-module','representation learning module',106,253,493,41,32)
line('reconstruction-bracket',[(831,231),(852,248),(1551,248),(1574,231)],'#444444',1.6)
text('reconstruction-module','reconstruction module',1056,253,478,41,32)
line('sr-branch',[(753,142),(753,312),(839,312)],'#222222',3,True,size=10)
# White backplate for the source stop-gradient symbol on branch.
rect('stop-gradient-back',743,246,20,25,'#FFFFFF','none',0)
text('stop-gradient','ø',740,243,25,35,28,italic=True)
text('psi','ψ',758,199,42,45,39,italic=True)
for k,x1,x2 in [(1,873,914),(2,956,997)]:
 line('sr-forward-'+str(k),[(x1,312),(x2,312)],'#333333',2.7,True,size=10);text('sr-fc-'+str(k),'fc',x1,284,x2-x1,25,21)
text('sr-relu-0','ReLU',765,323,70,27,21);text('sr-relu-1','ReLU',864,323,61,27,21)
for k,x,label in [(1,820,'2048'),(2,902,'1024'),(3,985,'2048')]:text('sr-dimension-'+str(k),label,x,372,66,25,21)
line('sr-bracket',[(808,378),(831,397),(1040,397),(1059,378)],'#444444',1.6)
text('sr-title','SR estimator',626,357,178,39,32)
finish()
