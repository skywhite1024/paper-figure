"""Prepare one source-hash-bound paper candidate; does not approve visual QA."""
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from paper_figure.model import load, require
from paper_figure.outputs import sha256

def prepare(slug,survey_path,scene_path,export_path,original,validation=None):
    import fitz
    require(bool(re.fullmatch(r'[a-z0-9_-]+',slug)),'unsafe paper slug')
    survey=json.loads(Path(survey_path).read_text());scene_path=Path(scene_path).resolve();scene=load(scene_path)
    require(survey.get('title_match') is True,'Source title must be independently matched first')
    pdf=Path(survey['pdf_path']);pdf=pdf if pdf.is_absolute() else ROOT/pdf
    require(sha256(pdf)==survey['pdf_sha256'],'Source PDF bytes changed')
    require(scene['provenance'].get('source_sha256')==sha256(pdf),'Scene source PDF hash differs')
    doc=fitz.open(pdf);text='\n'.join(p.get_text() for p in doc)
    versions=re.findall(r'\d{4}\.\d{4,5}v\d+',text[:20000])
    version=next((v for v in versions if v in scene['provenance']['paper_url']),None)
    version=version or survey.get('version') or 'publisher-version'
    arxiv=re.search(r'arxiv.org/(?:abs|pdf)/(\d{4}\.\d{4,5}v\d+)',scene['provenance']['paper_url'])
    if arxiv:
        version=arxiv.group(1);require(version in text,'Fixed arXiv version not found in PDF')
    name=f'{slug}-{version}.pdf' if re.fullmatch(r'[a-zA-Z0-9._-]+',version) else slug+'-source.pdf'
    candidate=ROOT/'build/candidates'/slug;candidate.mkdir(parents=True,exist_ok=True)
    stem=scene['id']
    for suffix in ['.pptx','.drawio','.png','.manifest.json']:
        shutil.copy2(Path(export_path)/(stem+suffix),candidate/(stem+suffix))
    shutil.copy2(pdf,candidate/name);shutil.copy2(original,candidate/(slug+'-original.png'))
    metadata={'id':slug,'title':survey['title_expected'],'file':name,'source_url':('https://arxiv.org/pdf/'+version if arxiv else survey.get('pdf_url',survey['source_url'])),
              'sha256':sha256(pdf),'bytes':pdf.stat().st_size,'page_count':len(doc),
              'figure':scene['provenance']['figure'],'pdf_page_1_based':scene['provenance']['page'],
              'diagram_json':'../../'+str(scene_path.relative_to(ROOT)),'editable_pptx':stem+'.pptx','editable_drawio':stem+'.drawio',
              'source_version':version,'all_pages_readable':True,'embedded_version_verified':bool(arxiv),'catalog_id':survey['catalog_id']}
    if arxiv:metadata['arxiv_id_version']=version
    sources={'purpose':'User-requested private source comparison and editable reconstruction','rights_note':'Retain author attribution and source license; private conversion does not grant public redistribution rights.','papers':[metadata]}
    (candidate/'sources.json').write_text(json.dumps(sources,indent=2,ensure_ascii=False)+'\n')
    if validation:shutil.copy2(validation,candidate/'VALIDATION.json')
    else:(candidate/'VALIDATION.json').write_text(json.dumps({'review_status':'pending independent source/editor review','scene_sha256':sha256(scene_path)},indent=2)+'\n')
    return str(candidate)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['slug','survey','scene','export','original']:p.add_argument('--'+arg,required=True)
    p.add_argument('--validation')
    a=p.parse_args();print(prepare(a.slug,a.survey,a.scene,a.export,a.original,a.validation))
