import argparse,json,sys
from pathlib import Path
from .model import load,metrics,require,ValidationError,STATUSES
from .exporters import export

def read_catalog(path):
 c=json.loads(Path(path).read_text());require(isinstance(c,dict) and type(c.get('schema_version')) is int and c['schema_version']==1,'invalid catalog');require(isinstance(c.get('papers'),list),'papers required');ids=set()
 for p in c['papers']:
  require(isinstance(p,dict) and isinstance(p.get('id'),str) and p['id'] not in ids,'invalid/duplicate paper ID');ids.add(p['id']);require(isinstance(p.get('status'),str) and p['status'] in STATUSES,'invalid paper status')
  for key in ['title','url']:require(isinstance(p.get(key),str) and p[key].strip(),'paper '+key+' required')
  if p['status'] in ['recreated','verified']:require(isinstance(p.get('diagram'),str) and p['diagram'],'completed paper requires diagram')
 return c

def batch(path,out,formats,force=False,preview=False):
 root=Path(path).resolve().parent;result={'exported':[],'skipped':[],'failed':[]}
 for p in read_catalog(path)['papers']:
  if p['status'] not in ['recreated','verified']:result['skipped'].append({'id':p['id'],'status':p['status']});continue
  try:
   f=(root/p['diagram']).resolve();require(f.is_relative_to(root),'diagram escapes catalog');require('/' not in p['id'] and '\\' not in p['id'] and p['id'] not in ['.','..'],'unsafe paper id');r=export(load(f),f,Path(out)/p['id'],formats,force,preview);result['exported'].append({'id':p['id'],'metrics':r['metrics']})
  except (OSError,ValidationError) as exc:result['failed'].append({'id':p['id'],'error':str(exc)})
 return result

def main(argv=None):
 p=argparse.ArgumentParser(prog='paper-figure');sub=p.add_subparsers(dest='cmd',required=True)
 for name in ['validate','export','catalog','batch']:
  s=sub.add_parser(name);s.add_argument('path',type=Path)
  if name in ['export','batch']:s.add_argument('--out',type=Path,default=Path('build'));s.add_argument('--format',choices=['drawio','pptx','both'],default='both');s.add_argument('--force',action='store_true');s.add_argument('--preview',action='store_true')
 a=p.parse_args(argv)
 try:
  if a.cmd=='validate':r=metrics(load(a.path))
  elif a.cmd=='catalog':
   c=read_catalog(a.path);r={'total':len(c['papers']),'statuses':{s:sum(x['status']==s for x in c['papers']) for s in sorted(STATUSES)}}
  else:
   fmts=('drawio','pptx') if a.format=='both' else (a.format,);r=batch(a.path,a.out,fmts,a.force,a.preview) if a.cmd=='batch' else export(load(a.path),a.path,a.out,fmts,a.force,a.preview)
  print(json.dumps(r,ensure_ascii=False,indent=2));return 1 if a.cmd=='batch' and r['failed'] else 0
 except (ValidationError,OSError,json.JSONDecodeError) as e:print('error:',e,file=sys.stderr);return 2
