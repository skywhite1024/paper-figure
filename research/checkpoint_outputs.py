"""Reconcile verified local bundles with catalog/queue; never claim editor QA."""
import json
import re
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from paper_figure.outputs import read_paper, refresh_output
from paper_figure.queue import read_checkpoint, update_checkpoint, queue_status
from paper_figure.model import require

def sync(root=ROOT):
    root=Path(root);catalog_path=root/'data/catalog.json';catalog=json.loads(catalog_path.read_text())
    papers=catalog['papers'];processed=[]
    for source in sorted((root/'output').glob('*/sources.json')):
        folder=source.parent;paper,scene,manifest,original=read_paper(folder,root)
        rows=[p for p in papers if p['id']==paper.get('catalog_id')]
        if not rows:
            version=paper.get('arxiv_id_version','');base=re.sub(r'v\d+$','',version)
            rows=[p for p in papers if base and base in p['url']]
        if not rows:
            rows=[p for p in papers if (p.get('diagram') and (root/'data'/p['diagram']).resolve()==(folder/paper['diagram_json']).resolve())]
        require(len(rows)==1,'Cannot resolve unique catalog record for '+folder.name)
        row=rows[0];diagram=str((folder/paper['diagram_json']).resolve().relative_to(root/'data'))
        row.update(status='recreated',diagram=diagram,output_directory=str(folder.relative_to(root)))
        row['notes']='Source-linked editable reconstruction delivered; precise source, raster/editability boundaries and performed/pending QA are recorded in the per-paper output folder. Recreated does not imply pixel-exact or fully editor-verified.'
        checkpoint=read_checkpoint(root,row['id'])
        evidence={'summary':'Complete local source-linked editable bundle; application QA limits remain explicit in per-paper report.',
                  'references':[str((folder/'README.md').relative_to(root)),str((folder/'VALIDATION.json').relative_to(root))],
                  'output_directory':str(folder.relative_to(root)), 'source_sha256':paper['sha256'], 'scene_sha256':manifest['source_sha256']}
        existing=checkpoint['stages']['recreation']
        if existing.get('evidence')!=evidence or checkpoint['status']!='recreated':
            update_checkpoint(root,row['id'],{'status':'recreated','stages':{'recreation':{'status':'reported','evidence':evidence}}},actor='bundle-integration')
        processed.append(folder.name)
    catalog_path.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
    refresh_output(root)
    summary={'catalog_total':len(papers),'delivered_recreations':len(processed),'output_folders':processed,
             'catalog_status':dict(Counter(p['status'] for p in papers)), 'queue':queue_status(root),
             'qa_note':'Recreated/delivered means source-linked native editable files exist; see each VALIDATION.json for actual source/editor checks. Draw.io application rendering can remain pending independently of structural validation.'}
    (root/'output/PROCESSING.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    return summary
if __name__=='__main__':print(json.dumps(sync(),indent=2,ensure_ascii=False))
