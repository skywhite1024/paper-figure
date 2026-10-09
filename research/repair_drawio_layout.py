"""Regenerate draw.io-only native layout after exporter fixes; preserve PPTX/PNG bytes."""
import copy
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from paper_figure.outputs import read_paper,sha256,refresh_output
from paper_figure.exporters import drawio

def repair(root=ROOT):
    root=Path(root);updated=[]
    for sources in sorted((root/'output').glob('*/sources.json')):
        folder=sources.parent;paper,scene,manifest,_=read_paper(folder,root)
        source=(folder/paper['diagram_json']).resolve();name=scene['id']+'.drawio'
        with tempfile.TemporaryDirectory() as tmp:
            generated=Path(tmp)/name;drawio(scene,generated,source.parent);ET.parse(generated)
            if sha256(generated)==sha256(folder/name):continue
            previous=sha256(folder/name);(folder/name).write_bytes(generated.read_bytes())
        entry=next(e for e in manifest['files'] if e['name']==name);entry['sha256']=sha256(folder/name)
        (folder/(scene['id']+'.manifest.json')).write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
        qa_path=folder/'VALIDATION.json';qa=json.loads(qa_path.read_text())
        for entry in qa.get('checked_files',[]):
            if entry['name']==name:entry['sha256']=sha256(folder/name)
        qa['drawio_layout_revalidation']={'previous_sha256':previous,'current_sha256':sha256(folder/name),
            'xml_parse':'passed','change':'Exporter now honors source no_wrap and text_inset. Source nodes/labels/paths and PPTX/PNG bytes unchanged.',
            'application_render':'not performed; isolated application display unavailable'}
        qa_path.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n');updated.append(folder.name)
    refresh_output(root)
    return updated
if __name__=='__main__':print(json.dumps({'updated':repair()},indent=2))
