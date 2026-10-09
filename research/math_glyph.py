"""Native STIX mathematical glyph outlines for explicitly reviewed transcriptions."""
import os,tempfile
os.environ.setdefault('MPLCONFIGDIR',tempfile.mkdtemp(prefix='paper-figure-math-'))
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib import rc_context

def glyph_node(id,latex,x,y,width,height,color='#111111'):
    with rc_context({'mathtext.fontset':'stix'}):p=TextPath((0,0),'$'+latex+'$',size=30,prop=FontProperties(family='STIXGeneral'))
    b=p.get_extents();commands=[]
    def xy(a,c):return dict(x=(a-b.x0)/b.width*width,y=(b.y1-c)/b.height*height)
    for v,k in p.iter_segments(curves=True,simplify=False):
        if k==1:commands.append({'moveTo':xy(*v)})
        elif k==2:commands.append({'lineTo':xy(*v)})
        elif k==3:
            a=xy(*v[:2]);e=xy(*v[2:]);commands.append({'quadBezTo':dict(x1=a['x'],y1=a['y'],**e)})
        elif k==4:
            a=xy(*v[:2]);c=xy(*v[2:4]);e=xy(*v[4:]);commands.append({'cubicBezTo':dict(x1=a['x'],y1=a['y'],x2=c['x'],y2=c['y'],**e)})
        elif k==79:commands.append({'close':{}})
    return dict(id=id,shape='path',x=x,y=y,width=width,height=height,commands=commands,fill=color,stroke='none',math_source=latex)
