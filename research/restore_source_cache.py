"""Restore ignored PDF caches from verified per-paper output archives, without network.

Default is a read-only plan. --apply copies missing identical-version PDFs and
updates existing survey pdf_path fields to portable repository-relative paths.
Existing cache files with different bytes are never overwritten.
"""
import argparse,hashlib,json,os,re,shutil,tempfile
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def restore(root,apply=False,paper=None):
    root=Path(root).resolve();catalog=json.loads((root/'data/catalog.json').read_text());results=[]
    for row in catalog['papers']:
        output=row.get('output_directory')
        if not output:continue
        folder=(root/output).resolve()
        require(folder.is_relative_to(root/'output') and folder.parent==root/'output','Unsafe output directory')
        if paper and paper not in (row['id'],folder.name):continue
        cid=row['id'];require(bool(re.fullmatch(r'[a-z0-9][a-z0-9_-]*',cid)),'Unsafe catalog ID')
        if (folder/'sources.json').exists():
            papers=json.loads((folder/'sources.json').read_text())['papers'];require(len(papers)==1,'One source paper per folder required');meta=papers[0];name=meta['file'];expected=meta['sha256']
        elif (folder/'disposition.json').exists():
            meta=json.loads((folder/'disposition.json').read_text());name=meta['source_file'];expected=meta['source_sha256']
        else:continue
        require(Path(name).name==name and name.lower().endswith('.pdf'),'Unsafe source PDF filename')
        source=(folder/name).resolve();require(source.is_relative_to(folder),'Source PDF escapes output folder')
        require(sha(source)==expected,'Archived PDF hash changed: '+str(source))
        with source.open('rb') as f:require(f.read(5)==b'%PDF-','Source is not a PDF')
        target=(root/'build/sources'/(cid+'.pdf')).resolve();require(target.is_relative_to(root/'build/sources'),'Source cache escapes repository')
        exists=target.exists()
        if exists:require(target.is_file() and sha(target)==expected,'Different cached source exists; refusing overwrite: '+str(target))
        survey=root/'research/survey'/(cid+'.json');record=json.loads(survey.read_text()) if survey.exists() else None
        if record is not None:require(record.get('pdf_sha256')==expected,'Survey source version differs from archived PDF: '+cid)
        if apply:
            target.parent.mkdir(parents=True,exist_ok=True)
            if not exists:
                fd,temp=tempfile.mkstemp(prefix='.restore-',suffix='.pdf',dir=target.parent);os.close(fd)
                try:
                    shutil.copyfile(source,temp);require(sha(Path(temp))==expected,'Source changed during copy');os.replace(temp,target)
                finally:
                    if os.path.exists(temp):os.unlink(temp)
            if record is not None:
                record['pdf_path']=str(target.relative_to(root));survey.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
        results.append(dict(catalog_id=cid,source=str(source.relative_to(root)),target=str(target.relative_to(root)),sha256=expected,action='already_present' if exists else ('restored' if apply else 'would_restore')))
    require(not paper or results,'No matching archived paper found')
    return results
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--paper');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    print(json.dumps(restore(a.root,a.apply,a.paper),indent=2))
