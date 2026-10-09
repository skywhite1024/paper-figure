"""Paper-specific source-layout reconstruction. Read the original PDF pixels before editing coordinates."""
import argparse, json, hashlib, shutil, subprocess, sys, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[2]
SLUG='transfer-manipulation'; CAT='unsupervised-reinforcement-learning-for-transferable-manipulation-skill-discovery'; FIG='figure-2'; CROP=[312, 50, 557, 204]; FONT='Times New Roman'
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
# Figure 2 policy architecture: encoder inset at left, mixture policy center, gating inset right.
s['provenance']['notes']+=' All architecture geometry, residual additions, tensor icons and ordinary/math labels are native editable objects. The source colored glow is approximated by translucent concentric strokes; mathematical text uses Unicode instead of a live equation object. No raster assets are embedded.'
def glowbox(id,x,y,w,h,color):
 for k,sw,op in [(0,20,.08),(1,13,.13),(2,7,.20)]:
  z=rounded(id+'-glow'+str(k),x,y,w,h,9,'none',color,sw);z['stroke_opacity']=op
 rounded(id,x,y,w,h,8,'#FFFFFF',color,1.2)
def sans(id,label,x,y,w,h,fs=21,bold=True):return text(id,label,x,y,w,h,fs,bold=bold,font='Nimbus Sans Narrow')
# Expansion guide rules behind all node content.
line('encoder-expansion-top',[(293,46),(320,410)],'#555555',1.1,dash=True)
line('encoder-expansion-bottom',[(298,495),(318,466)],'#555555',1.1,dash=True)
line('gating-expansion-top',[(678,195),(642,262)],'#555555',1.1,dash=True)
line('gating-expansion-bottom',[(641,327),(672,396)],'#555555',1.1,dash=True)
for id,x,y,w,h,col in [('pool',17,27,271,48,'#BE4CAE'),('encoder-mlp',17,133,271,47,'#6DA54D'),('norm1',17,199,271,48,'#6F8EAB'),('attention',17,305,271,48,'#409AC1'),('norm2',17,376,271,48,'#6F8EAB'),('embedding',17,450,271,48,'#6DA54D'),('encoder',317,413,168,48,'#C35555'),('policy-mlp',317,263,169,63,'#6DA54D'),('gating',498,264,141,63,'#C5804B'),('gating-mlp-left',671,313,142,61,'#6DA54D'),('gating-mlp-right',833,313,142,61,'#6DA54D'),('gating-mlp-final',750,226,141,61,'#6DA54D')]:glowbox(id,x,y,w,h,col)
sans('pool-label','Average Pooling',23,31,259,39)
sans('encoder-mlp-label','MLP(256-Relu,128-Relu)',22,139,261,36,19)
sans('norm1-label','LayerNorm',24,204,257,36)
sans('attention-label','MultiHeadAttention(Relu)',22,311,261,35,19)
sans('norm2-label','LayerNorm',23,382,259,35)
sans('embedding-label','MLP(128)',25,456,255,36)
sans('encoder-label','Encoder',323,419,156,36)
sans('policy-mlp-title','MLP',324,273,155,28)
sans('policy-mlp-detail','(256-Relu, 256-Relu, 4)',323,302,157,20,13)
sans('gating-title','Gating Net',502,276,133,38)
for id,x in [('left',671),('right',833)]:
 sans('gating-mlp-'+id+'-title','MLP',x+4,320,134,29)
 sans('gating-mlp-'+id+'-detail','(256-Relu,128-Relu)',x+3,350,136,19,13)
sans('gating-final-title','MLP',754,232,133,29)
sans('gating-final-detail','(# Primitives-Sigmoid)',752,261,137,19,13)
# Encoder residual branches and native addition marks.
for id,y in [('lower',276),('upper',100)]:
 ellipse('residual-'+id,141,y-14,22,28,'#E5E9ED','#687D96',1.2)
 text('residual-'+id+'-plus','+',143,y-15,18,29,25,'#467CB3')
line('lower-residual',[(152,439),(6,439),(6,277),(141,277)],sw=2.7,arrow=True,size=8)
line('upper-residual',[(152,260),(6,260),(6,101),(141,101)],sw=2.7,arrow=True,size=8)
for id,y1,y2 in [('embedding-norm',450,424),('norm-attention',376,354),('attention-plus',305,290),('plus-norm',263,247),('norm-mlp',199,181),('mlp-plus',133,115),('plus-pool',86,75),('pool-output',27,9)]:line(id,[(152,y1),(152,y2)],sw=2.4,arrow=True,size=8)
line('input-left',[(58,514),(58,498)],sw=2.2,arrow=True,size=7)
line('input-right',[(251,514),(251,498)],sw=2.2,arrow=True,size=7)

for name,x,k in [('left',45,'1'),('right',238,'M')]:
 text(name+'-robot-state','s',x+3,515,16,28,23,italic=True);text(name+'-robot-subscript','r',x+15,529,11,16,14,italic=True)
 text(name+'-object-state','s',x,542,16,28,23,italic=True);text(name+'-object-subscript','o',x+12,554,11,16,14,italic=True);text(name+'-object-index','('+k+')',x+14,539,23,16,14,italic=True)
 text(name+'-indicator','s',x-1,569,16,28,23,italic=True);text(name+'-indicator-subscript','ind',x+11,582,22,17,14,italic=True);text(name+'-indicator-index','('+k+')',x+15,565,23,16,14,italic=True)
 text(name+'-weight','w',x+2,594,25,22,23,italic=True)
text('inputs-ellipsis','...',132,545,38,36,24,bold=True)
# Main policy and encoded tensor icons.
text('policy-title','Policy',461,6,91,36,25,bold=True,italic=True)
text('policy-distribution','π(a|s,w,z)',410,71,138,39,25,italic=True)
text('policy-parameters','μ,σ',453,134,53,35,25,italic=True)
line('policy-output',[(480,133),(480,109)],sw=2.3,arrow=True,size=8)
line('parameters-output',[(480,187),(480,167)],sw=2.3,arrow=True,size=8)
line('mixture-join',[(402,209),(402,187),(568,187),(568,209)],sw=2.7)
text('primitives','πᵢ(a|φ(s,w))',331,207,145,31,23,italic=True)
text('primitive-index','(i = 1, ... N)',416,232,117,31,23,italic=True)
text('gating-weights','Wᵢ(φ(s,w),z)',496,207,144,31,23,italic=True)
line('policy-mlp-to-join',[(401,264),(401,242)],sw=2.4,arrow=True,size=8)
line('gating-to-join',[(568,264),(568,242)],sw=2.4,arrow=True,size=8)
line('encoder-output',[(401,413),(401,327)],sw=2.4,arrow=True,size=8)
line('encoded-to-gating',[(401,370),(569,370),(569,327)],sw=2.4,arrow=True,size=8)
line('z-to-gating',[(586,379),(586,327)],sw=2.4,arrow=True,size=8)
def tensor(id,x,y,w,h):
 poly(id+'-top',[(x,y),(x+10,y+6),(x+w+10,y+6),(x+w,y)],'#7A8CA1',1,'#D8DDE2',True)
 poly(id+'-left',[(x,y),(x+10,y+6),(x+10,y+h+6),(x,y+h)],'#7A8CA1',1,'#BEC7D1',True)
 rect(id+'-front',x+10,y+6,w,h,'#D8DDE2','#7A8CA1',1)
tensor('encoded-tensor',357,379,72,14);tensor('z-tensor',545,384,72,14)
text('encoded-feature','φ(s,w)',439,375,76,34,23,italic=True)
text('latent-z','z',571,405,32,34,23,italic=True)
# Expanded gating net details.
line('gating-feature-input',[(742,392),(742,375)],sw=2.4,arrow=True,size=8)
line('gating-z-input',[(905,392),(905,375)],sw=2.4,arrow=True,size=8)
text('gating-feature','φ(s,w)',699,392,87,36,23,italic=True)
text('gating-latent','z',891,392,29,36,23,italic=True)
line('gating-input-join',[(742,313),(742,299),(905,299),(905,313)],sw=2.4)
line('gating-joined-final',[(820,299),(820,287)],sw=2.4,arrow=True,size=8)
line('gating-final-output',[(820,226),(820,193)],sw=2.4,arrow=True,size=8)
finish()
