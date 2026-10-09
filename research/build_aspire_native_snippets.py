"""Native editable replacement of two raster source mini-panels, inspected 2026-10-09."""
import json
from pathlib import Path
S={'remove_source_seqnos':[8,116],'nodes':[],'edges':[],'notes':'Manually recreated source code and evolutionary-search inset from actual PDF page2 pixels. Native panels/text/connectors; Consolas/Arial substitutions and arrow/dash spacing approximated.'}
def n(id,label,x,y,w,h,fill='#FFFFFF',stroke='#FFFFFF',shape='rect',font=4.5,**kw):
 z=dict(id='snippet-'+id,label=label,x=(x-61)*3,y=(y-84)*3,width=w*3,height=h*3,fill=fill,stroke=stroke,shape=shape,font_size=font*3,**kw);S['nodes'].append(z);return z['id']
def text(id,label,x,y,w,h,font=4.5,color='#111111',family='Arial',bold=False):return n(id,label,x,y,w,h,shape='text',font=font,text_color=color,font_family=family,align='left',bold=bold,text_inset=0,no_wrap=True)
def edge(id,a,b,arrow=True,color='#8A3C0D',width=.7,dash=False):S['edges'].append(dict(id='snippet-'+id,source=a,target=b,source_port='bottom',target_port='top',arrow=arrow,stroke=color,stroke_width=width*3,dash=dash))
def anchor(id,x,y):return n(id,'',x,y,.02,.02,'none','none',stroke_width=0)
# Four-line editable code review panel.
x,y,w,h=441.3518,116.7611,81.4999,32.5764
n('code-bg','',x,y,w,h,'#FFFEFF','#F6C6AC','rounded_rect',stroke_width=.3*3)
n('code-removed','',x+.25,y+7.8,w-.5,8.5,'#FEF2F3','#FEF2F3',stroke_width=0)
n('code-added','',x+.25,y+24.35,w-.5,7.7,'#EFFAF1','#EFFAF1','rounded_rect',stroke_width=0)
rows=[('open_gripper','',None),('move_to_joints','lift_pos','-'),('move_to_joints','grasp_pos',None),('close_gripper','', '+')]
for i,(func,arg,sign) in enumerate(rows):
 yy=y+1.0+i*8.2
 text('lineno'+str(i),str(i+1),445.1,yy,5.0,6.3,4.3,'#7B7B7B','Consolas')
 if sign:text('change'+str(i),sign,452.0,yy,5.1,6.3,4.5,'#DC2626' if sign=='-' else '#2CB341','Consolas',True)
 fx=459.2; char=2.52
 text('function'+str(i),func,fx,yy,len(func)*char+1,6.3,4.45,'#8150F1','Consolas')
 px=fx+len(func)*char
 text('parenopen'+str(i),'(',px,yy,3,6.3,4.45,'#EBC900','Consolas')
 if arg:text('argument'+str(i),arg,px+char,yy,len(arg)*char+1,6.3,4.45,'#4E4E4E','Consolas')
 text('parenclose'+str(i),')',px+char*(1+len(arg)),yy,3,6.3,4.45,'#EBC900','Consolas')
# The original iterative-debugging title outside image stays native in main extracted scene.
x,y,w,h=442.9,165.4,77.5,50.4
n('search-bg','',x,y,w,h,'#FBE4D7','#E97837','rounded_rect',stroke_width=1.0*3,dash=True)
# Top-row descendants from preceding generation (three orange dashed spokes).
root=anchor('old-root',481.6,168.25)
for i,(xx,yy) in enumerate([(452.0,174.4),(485.7,175.0),(498.5,174.4)]):edge('old-spoke'+str(i),root,anchor('old-target'+str(i),xx,yy),False,'#E97837',.4,True)
text('iter-n','iter N',503.7,167.2,16.4,6.1,5.0,'#000000',bold=True)
text('iter-next','iter N + 1',498.5,192.6,23.4,6.0,5.0,'#000000')
# Original Pi nodes retain red / green / red candidates and black descendants.
xs=[445.6,465.7,498.6]
for i,xx in enumerate(xs):
 n('parent'+str(i),'',xx,177.0,11.2,10.6,'#F7C7A9','#E97837','rounded_rect',stroke_width=.4*3)
 n('child'+str(i),'',xx,202.5,12.0,10.6,'#F7C7A9','#E97837','rounded_rect',stroke_width=.4*3)
 color='#00B43B' if i==1 else '#FF0000'
 label=['π₀','π₁','πₖ'][i]
 text('parent-text'+str(i),label,xx+.5,177.05,11.0,10.2,8.0,color,'Arial')
 text('child-text'+str(i),['π₀′','π₁′','πₖ′'][i],xx+.3,202.55,11.8,10.2,7.7,'#000000','Arial')
text('parent-ellipsis','…',482.2,180.6,10.4,9,9.0,'#000000',bold=True)
text('child-ellipsis','…',482.2,204.4,10.4,9,9.0,'#000000',bold=True)
# Brown fan-out begins at central successful candidate; native semantic connectors.
root2=anchor('search-root',471.1,189.25)
for i,xx in enumerate(xs):edge('new-spoke'+str(i),root2,anchor('new-target'+str(i),xx+6,201.0),True,'#8D3D0A',.7)
# Keep each full code line in one editable text frame so substituted fonts
# cannot overlap independently positioned syntax tokens.
old_nodes=S['nodes']
S['nodes']=[n for n in old_nodes if not any(n['id'].startswith('snippet-'+prefix) for prefix in ['function','parenopen','parenclose','argument'])]
for i,label in enumerate(['open_gripper()','move_to_joints(lift_pos)','move_to_joints(grasp_pos)','close_gripper()']):
 n=next(n.copy() for n in old_nodes if n['id']=='snippet-function'+str(i))
 n.update(id='snippet-code-line'+str(i),label=label,width=190,font_size=12,font_family='Courier New',text_color='#7030A0',text_inset=0,no_wrap=True,align='left')
 S['nodes'].append(n)
S['notes']=S.get('notes','')+' Code lines use one native monospaced text object each; token colors simplified to prevent overlap when fonts substitute.'
Path(__file__).with_name('aspire-native-snippets.json').write_text(json.dumps(S,indent=2,ensure_ascii=False))
print(len(S['nodes']),'nodes',len(S['edges']),'edges')
