"""Source-layout native reconstruction of ARO Fig1; source raster visually inspected."""
from pathlib import Path
import json,hashlib,fitz
R=Path(__file__).resolve().parents[2];slug='aro-figure-1';D=R/'data/diagrams'/slug;D.mkdir(parents=True,exist_ok=True)
ev=json.loads(next((R/'research/survey').glob('aro-large*.json')).read_text());pdf=R/ev['pdf_path']
s=dict(schema_version=1,id=slug,title='ARO framework — native editable reconstruction',canvas=dict(width=1380,height=375),provenance=dict(paper_title=ev['title_expected'],paper_url='https://arxiv.org/abs/'+ev['version'],figure='Figure 1',page=2,license=ev['license_note'],notes='Manually recreated from actual original 1380×338 Figure1 raster. All module boxes, labels, document icons, human outlines and arrows are native objects; no full-figure raster backdrop. Font, icon outlines and corner curvature are approximate. Native freeform return loop is not automatically attached to module endpoints.',status='figure_recreation',source_sha256=ev['pdf_sha256'],source_crop_pdf_points=[344,429,524,472],visual_inspection='Original PDFpage2 and embedded1380×338 figure pixels inspected2026-10-09'),nodes=[],edges=[])
def n(id,label,x,y,w,h,fill='#F4F5FC',stroke='#111111',shape='rect',fs=18,**kw):
 s['nodes'].append(dict(id=id,label=label,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,shape=shape,font_size=fs,font_family='Arial',text_color='#292D32',bold=True,text_inset=0,**kw));return id
def t(id,label,x,y,w,h,fs=18):return n(id,label,x,y,w,h,shape='text',fs=fs,align='left',no_wrap=True)
def path(id,x,y,w,h,cmds,fill='none',stroke='#111111',width=2.5):return n(id,'',x,y,w,h,fill,stroke,'path',commands=cmds,stroke_width=width)
def e(id,src,tgt,sp='right',tp='left'):s['edges'].append(dict(id=id,source=src,target=tgt,source_port=sp,target_port=tp,arrow=True,stroke='#111111',stroke_width=2.2))
def anchor(id,x,y):return n(id,'',x,y,.1,.1,fill='none',stroke='none',stroke_width=0)
# Main module positions copied from original pixels.
for id,label,x,y,w,h in [('rfg','RFG\n(LLM-based)',307,39,135,122),('rl','Training\n(RL)',587,37,135,126),('efg','EFG\n(LLM-based)',886,37,135,126),('pe','PE\n(LLM-based)',1170,37,135,126),('ee','EE\n(LLM-based)',307,194,135,72)]:n(id,label,x,y,w,h,shape='rounded_rect',fs=17,stroke_width=2.4)
e('rfg-train','rfg','rl');e('train-efg','rl','efg');e('efg-pe','efg','pe');e('ee-rfg','ee','rfg','top','bottom')
# Editable folded documents with inset T/code labels.
def document(id,x,y,code=False,gray=False):
 w,h=37,46;cmd=[{'moveTo':{'x':0,'y':0}},{'lineTo':{'x':25,'y':0}},{'lineTo':{'x':37,'y':12}},{'lineTo':{'x':37,'y':46}},{'lineTo':{'x':0,'y':46}},{'close':{}}];path(id,x,y,w,h,cmd,'#BFC3C7' if gray else '#FFFFFF',width=3)
 path(id+'-fold',x+25,y,12,12,[{'moveTo':{'x':0,'y':0}},{'lineTo':{'x':0,'y':12}},{'lineTo':{'x':12,'y':12}}],width=3)
 t(id+'-label','‹›' if code else 'T',x+6,y+13,27,29,27)
document('task-document',82,77,gray=True);document('reward-document',457,111,True);document('evaluation-document',1032,111,True);document('env-document',147,207,True);document('feedback-document',1162,240)
# Human bust outlines preserve source role markers, now editable paths.
def person(id,x,y):
 path(id,x,y,46,47,[{'moveTo':{'x':0,'y':46}},{'lineTo':{'x':1,'y':39}},{'cubicBezTo':{'x1':4,'y1':34,'x2':14,'y2':35,'x':15,'y':30}},{'lineTo':{'x':15,'y':25}},{'cubicBezTo':{'x1':9,'y1':21,'x2':11,'y2':16,'x':12,'y':14}},{'cubicBezTo':{'x1':11,'y1':5,'x2':14,'y2':2,'x':20,'y':2}},{'cubicBezTo':{'x1':28,'y1':0,'x2':36,'y2':4,'x':34,'y':13}},{'cubicBezTo':{'x1':38,'y1':19,'x2':35,'y2':24,'x':31,'y':26}},{'lineTo':{'x':31,'y':31}},{'cubicBezTo':{'x1':34,'y1':35,'x2':43,'y2':35,'x':45,'y':41}},{'lineTo':{'x':46,'y':46}},{'close':{}}],'#FFFFFF',width=3)
person('task-person',23,76);person('agent-person',733,111)
t('task-desc','Task Description',135,108,169,29,17)
t('reward-code','RF Code',509,124,76,27,17)
t('agent-label','RL Agent',784,124,99,27,17)
t('evaluation-code','EF Code',1078,124,85,27,17)
t('env-code','Env Code',198,217,103,28,17)
t('improvement','Improvement\nSuggestion',1213,248,134,47,17)
e('task-rfg',anchor('task-start',132,100),'rfg')
e('env-ee',anchor('env-start',275,230),'ee')
# Rounded bottom feedback return exactly follows original spatial arrangement.
path('feedback-return',374,99,974,211,[{'moveTo':{'x':933,'y':1}},{'lineTo':{'x':958,'y':1}},{'cubicBezTo':{'x1':971,'y1':1,'x2':973,'y2':8,'x':973,'y':16}},{'lineTo':{'x':973,'y':194}},{'cubicBezTo':{'x1':973,'y1':206,'x2':970,'y2':211,'x':959,'y':211}},{'lineTo':{'x':16,'y':211}},{'cubicBezTo':{'x1':4,'y1':211,'x2':0,'y2':205,'x':0,'y':195}},{'lineTo':{'x':0,'y':174}}],width=2.2)
path('feedback-arrow',367,270,15,13,[{'moveTo':{'x':0,'y':9}},{'lineTo':{'x':7.5,'y':0}},{'lineTo':{'x':15,'y':9}}],width=2.2)
t('credit','Adapted from ARO (2024), Fig.1, p.2 · All diagram elements are native editable objects; typography and icon outlines approximate the source',22,345,1340,22,12)
(D/(slug+'.json')).write_text(json.dumps(s,indent=2,ensure_ascii=False))
d=fitz.open(pdf);im=d[1].get_images(full=True)[0];data=d.extract_image(im[0]);(D/(slug+'-original.png')).write_bytes(data['image'])
print(len(s['nodes']),'native nodes',len(s['edges']),'connectors')
