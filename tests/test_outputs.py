import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import os
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from paper_figure.model import ValidationError
from paper_figure.outputs import refresh_output, publish_build, sha256

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in {'href', 'src'})


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repository'
        self.root.mkdir()
        (self.root / 'output').mkdir()
        for path in (ROOT / 'output').iterdir():
            if path.is_file(): shutil.copy2(path, self.root / 'output' / path.name)
        for slug in ['aspire', 'roboreact']:
            shutil.copytree(ROOT / 'output' / slug, self.root / 'output' / slug)
        for metadata in (self.root / 'output').glob('*/sources.json'):
            record=json.loads(metadata.read_text())['papers'][0]
            relative=(metadata.parent/record['diagram_json']).resolve().relative_to(self.root)
            scene=ROOT/relative;target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(scene,target)
            for node in json.loads(scene.read_text())['nodes']:
                if node['shape']=='image':
                    asset=target.parent/node['asset'];asset.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(scene.parent/node['asset'],asset)
        self.output = self.root / 'output'

    def test_geometry_qa_rejects_stale_pptx_binding(self):
        folder = self.output / 'aspire'
        source = json.loads((folder / 'sources.json').read_text())['papers'][0]
        scene_path = (folder / source['diagram_json']).resolve()
        report = {'status': 'passed', 'scene_sha256': sha256(scene_path),
                  'pptx_sha256': '0' * 64}
        (folder / 'OOXML_GEOMETRY_QA.json').write_text(json.dumps(report))
        with self.assertRaisesRegex(ValidationError, 'geometry QA binds older'):
            refresh_output(self.root)

    def artifact_hashes(self):
        return {str(p.relative_to(self.output)): sha256(p)
                for p in self.output.rglob('*') if p.suffix in {'.pptx', '.drawio', '.png', '.pdf'}}

    def test_refresh_preserves_all_artifact_bytes(self):
        before = self.artifact_hashes()
        refresh_output(self.root)
        self.assertEqual(before, self.artifact_hashes())

    def test_each_paper_is_self_contained(self):
        self.assertFalse(any(p.suffix in {'.pdf', '.pptx', '.drawio', '.png'} for p in self.output.iterdir()))
        for slug, figure in [('aspire', 1), ('roboreact', 2)]:
            folder = self.output / slug
            paper = json.loads((folder / 'sources.json').read_text())['papers'][0]
            self.assertTrue((folder / paper['file']).is_file())
            for suffix in ['pptx', 'drawio', 'png', 'manifest.json']:
                self.assertTrue((folder / f'{slug}-figure-{figure}.{suffix}').is_file())
            self.assertTrue((folder / f'{slug}-original.png').is_file())

    def test_html_and_markdown_links_resolve(self):
        refresh_output(self.root)
        for path in self.output.rglob('*'):
            if path.suffix == '.html':
                parser = Links(); parser.feed(path.read_text()); links = parser.links
            elif path.suffix == '.md':
                links = re.findall(r'\]\(([^)]+)\)', path.read_text())
            else:
                continue
            for link in links:
                parsed = urlsplit(link)
                if parsed.scheme or not parsed.path:
                    continue
                self.assertTrue((path.parent / unquote(parsed.path)).resolve().is_file(), (path, link))

    def test_bundle_hashes_are_real(self):
        refresh_output(self.root)
        for manifest in self.output.glob('*/bundle.manifest.json'):
            record = json.loads(manifest.read_text())
            for entry in record['files']:
                path = manifest.parent / entry['name']
                self.assertEqual(sha256(path), entry['sha256'])
                self.assertEqual(path.stat().st_size, entry['bytes'])

    def test_refresh_is_idempotent(self):
        refresh_output(self.root)
        before = {str(p): sha256(p) for p in self.output.rglob('*') if p.is_file()}
        refresh_output(self.root)
        self.assertEqual(before, {str(p): sha256(p) for p in self.output.rglob('*') if p.is_file()})

    def test_corrupt_source_pdf_is_rejected(self):
        pdf = next((self.output / 'aspire').glob('*.pdf'))
        pdf.write_bytes(b'not the original PDF')
        with self.assertRaises(ValidationError):
            refresh_output(self.root)

    def test_missing_preview_is_rejected(self):
        (self.output / 'aspire/aspire-figure-1.png').unlink()
        with self.assertRaises(ValidationError):
            refresh_output(self.root)

    def test_stale_figure_page_mapping_rejected(self):
        path = self.output / 'aspire/sources.json'
        data = json.loads(path.read_text()); data['papers'][0]['pdf_page_1_based'] = 3
        path.write_text(json.dumps(data))
        with self.assertRaises(ValidationError):
            refresh_output(self.root)

    def make_build(self):
        build = self.root / 'build'
        for folder in self.output.iterdir():
            if folder.is_dir():
                (build / folder.name).mkdir(parents=True)
                for path in folder.glob('*'):
                    if path.suffix in {'.pptx', '.drawio'} or '-figure-' in path.name and path.suffix in {'.png', '.json'}:
                        shutil.copy2(path, build / folder.name / path.name)
        return build

    def test_publish_build_retains_paper_layout_and_pdfs(self):
        before = self.artifact_hashes()
        result = publish_build(self.root, self.make_build())
        self.assertEqual(result['papers'], sorted(p.name for p in self.output.iterdir() if p.is_dir()))
        self.assertEqual(before, self.artifact_hashes())

    def test_changed_build_does_not_inherit_visual_approval(self):
        build = self.make_build()
        path = build / 'aspire/aspire-figure-1.drawio'
        path.write_bytes(path.read_bytes() + b'\n')
        manifest_path = build / 'aspire/aspire-figure-1.manifest.json'
        manifest = json.loads(manifest_path.read_text())
        next(e for e in manifest['files'] if e['name'] == path.name)['sha256'] = sha256(path)
        manifest_path.write_text(json.dumps(manifest))
        result = publish_build(self.root, build)
        self.assertTrue(result['artifacts_modified'])
        validation = json.loads((self.output / 'aspire/VALIDATION.json').read_text())
        self.assertEqual(validation['review_status'], 'pending after regeneration')

    def test_invalid_candidate_does_not_modify_published_files(self):
        build = self.make_build()
        before = {str(p): sha256(p) for p in self.output.rglob('*') if p.is_file()}
        path = build / 'aspire/aspire-figure-1.manifest.json'
        manifest = json.loads(path.read_text()); manifest['diagram_id'] = 'wrong-diagram'
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValidationError):
            publish_build(self.root, build)
        self.assertEqual(before, {str(p): sha256(p) for p in self.output.rglob('*') if p.is_file()})

    def test_archives_preserve_nested_layout(self):
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        (self.root / 'source-example.py').write_text('print("source")\n')
        subprocess.run(['git', 'add', 'source-example.py', 'data'], cwd=self.root, check=True)
        spec = importlib.util.spec_from_file_location('package_release', ROOT / 'research/package_release.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        results = module.create_packages(self.root, self.output, self.root / 'build/releases')
        complete = next(Path(path) for path, _, _ in results if '-complete.zip' in path)
        with zipfile.ZipFile(complete) as archive:
            names = archive.namelist()
            self.assertIn('output/aspire/aspire-figure-1.pptx', names)
            self.assertIn('output/roboreact/roboreact-figure-2.pptx', names)
            self.assertIn('output/aspire/aspire-2607.00272v1.pdf', names)
            self.assertIn('source-example.py', names)
            self.assertNotIn('samples/aspire-figure-1.pptx', names)
            self.assertFalse(any(name.startswith('source/output/') for name in names))

            restored = self.root / 'restored'
            archive.extractall(restored)
            for metadata in (restored / 'output').glob('*/sources.json'):
                paper = json.loads(metadata.read_text())['papers'][0]
                for key in ['diagram_json', 'editable_pptx', 'editable_drawio']:
                    self.assertTrue((metadata.parent / paper[key]).resolve().is_file(), key)

    def test_non_arxiv_source_display(self):
        path=self.output/'aspire/sources.json'
        record=json.loads(path.read_text());record['papers'][0].pop('arxiv_id_version')
        record['papers'][0]['source_version']='Publisher final version'
        path.write_text(json.dumps(record));refresh_output(self.root)
        self.assertIn('Publisher final version',(path.parent/'README.md').read_text())
    def test_selected_build_does_not_require_other_papers(self):
        build=self.make_build();shutil.rmtree(build/'roboreact')
        before=self.artifact_hashes()
        result=publish_build(self.root,build,papers=['aspire'])
        self.assertFalse(result['artifacts_modified'])
        self.assertEqual(before,self.artifact_hashes())
    def test_unknown_selection_rejected(self):
        with self.assertRaises(ValidationError): publish_build(self.root,self.make_build(),papers=['missing'])

    def test_add_invalid_paper_does_not_touch_outputs(self):
        from paper_figure.outputs import add_paper
        candidate=self.root/'build/new-paper';candidate.mkdir(parents=True)
        (candidate/'sources.json').write_text('{"papers":[]}')
        before={str(p):sha256(p) for p in self.output.rglob('*') if p.is_file()}
        with self.assertRaises(ValidationError):add_paper(self.root,candidate)
        self.assertEqual(before,{str(p):sha256(p) for p in self.output.rglob('*') if p.is_file()})

    def test_add_existing_paper_rejected(self):
        from paper_figure.outputs import add_paper
        with self.assertRaises(ValidationError):add_paper(self.root,self.output/'aspire')

    def test_batch_add_validates_all_before_publication(self):
        from paper_figure.outputs import add_papers
        good=self.root/'build/new-paper';good.parent.mkdir(parents=True)
        shutil.copytree(self.output/'aspire',good)
        metadata=json.loads((good/'sources.json').read_text());metadata['papers'][0]['id']='new-paper'
        (good/'sources.json').write_text(json.dumps(metadata));(good/'aspire-original.png').rename(good/'new-paper-original.png')
        bad=self.root/'build/bad-paper';bad.mkdir();(bad/'sources.json').write_text('{"papers":[]}')
        before=(self.output/'README.md').read_bytes()
        with self.assertRaises(ValidationError):add_papers(self.root,[good,bad])
        self.assertFalse((self.output/'new-paper').exists());self.assertEqual(before,(self.output/'README.md').read_bytes())
        result=add_papers(self.root,[good]);self.assertEqual(result[0]['paper'],'new-paper')
        self.assertTrue((self.output/'new-paper/sources.json').exists())
    def test_duplicate_batch_slug_rejected(self):
        from paper_figure.outputs import add_papers
        with self.assertRaises(ValidationError):add_papers(self.root,[self.root/'a/new',self.root/'b/new'])

    def new_batch_candidate(self, slug):
        candidate=self.root/'build'/slug;candidate.parent.mkdir(exist_ok=True)
        shutil.copytree(self.output/'aspire',candidate)
        metadata=json.loads((candidate/'sources.json').read_text());metadata['papers'][0]['id']=slug
        (candidate/'sources.json').write_text(json.dumps(metadata))
        (candidate/'aspire-original.png').rename(candidate/(slug+'-original.png'))
        return candidate

    def test_batch_publication_rolls_back_on_second_directory_failure(self):
        from paper_figure.outputs import add_papers
        candidates=[self.new_batch_candidate(slug) for slug in ['one-new','two-new']]
        before={str(p.relative_to(self.output)):sha256(p) for p in self.output.rglob('*') if p.is_file()}
        replace=os.replace
        def fail_second(source,destination):
            if Path(destination)==self.output/'two-new':raise PermissionError('second directory failure')
            return replace(source,destination)
        with patch('paper_figure.outputs.os.replace',side_effect=fail_second):
            with self.assertRaisesRegex(PermissionError,'second directory'):add_papers(self.root,candidates)
        self.assertEqual(before,{str(p.relative_to(self.output)):sha256(p) for p in self.output.rglob('*') if p.is_file()})
        self.assertFalse((self.output/'one-new').exists());self.assertFalse((self.output/'two-new').exists())
        self.assertEqual(len(add_papers(self.root,candidates)),2)

    def test_batch_publication_restores_indexes_on_second_index_failure(self):
        from paper_figure.outputs import add_papers
        candidate=self.new_batch_candidate('one-new')
        before={str(p.relative_to(self.output)):sha256(p) for p in self.output.rglob('*') if p.is_file()}
        replace=os.replace
        def fail_second_index(source,destination):
            if Path(destination)==self.output/'comparison.html':raise PermissionError('second index failure')
            return replace(source,destination)
        with patch('paper_figure.outputs.os.replace',side_effect=fail_second_index):
            with self.assertRaisesRegex(PermissionError,'second index'):add_papers(self.root,[candidate])
        self.assertEqual(before,{str(p.relative_to(self.output)):sha256(p) for p in self.output.rglob('*') if p.is_file()})
        self.assertFalse((self.output/'one-new').exists())
        self.assertEqual(len(add_papers(self.root,[candidate])),1)

    def test_batch_rejects_dangling_destination_symlink(self):
        from paper_figure.outputs import add_papers
        candidate=self.new_batch_candidate('one-new')
        destination=self.output/'one-new';destination.symlink_to(self.root/'absent')
        with self.assertRaisesRegex(ValidationError,'already exists'):add_papers(self.root,[candidate])
        self.assertTrue(destination.is_symlink())

    def test_qa_tiers_bound_to_current_pptx_bytes(self):
        records={}
        for slug in ['aspire','roboreact']:
            folder=self.output/slug;paper=json.loads((folder/'sources.json').read_text())['papers'][0]
            scene=(folder/paper['diagram_json']).resolve()
            records[slug]={'scene_sha256':sha256(scene),'pptx_sha256':sha256(folder/paper['editable_pptx']),
                           'source_preview_native':'passed','libreoffice_render':'passed' if slug=='aspire' else 'pending','drawio_app_render':'pending'}
            stem=json.loads(scene.read_text())['id']
            records[slug]['hash_binding']={'source_scene_sha256':sha256(scene),'source_pdf_sha256':paper['sha256'],
                'exports':{stem+'.'+suffix:sha256(folder/(stem+'.'+suffix)) for suffix in ['pptx','drawio','png']}}
        path=self.output/'QA_SUMMARY.json';path.write_text(json.dumps({'papers':records}))
        refresh_output(self.root)
        self.assertIn('PPTX 实际 LibreOffice 打开与渲染：已通过 1，待完成 1',(self.output/'README.md').read_text())
        good=copy.deepcopy(records)
        records['aspire']['hash_binding']['exports']['aspire-figure-1.drawio']='0'*64
        path.write_text(json.dumps({'papers':records}));refresh_output(self.root)
        self.assertIn('检查汇总待更新',(self.output/'README.md').read_text())
        records=good
        records['aspire']['pptx_sha256']='0'*64;path.write_text(json.dumps({'papers':records}));refresh_output(self.root)
        self.assertIn('检查汇总待更新',(self.output/'README.md').read_text())

    def test_stale_qa_hash_rejected(self):
        path=self.output/'aspire/VALIDATION.json'
        path.write_text(json.dumps({'source_scene_sha256':'0'*64}))
        with self.assertRaises(ValidationError):refresh_output(self.root)


    def test_asset_change_without_scene_change_rejected(self):
        scene=self.root/'data/diagrams/aspire-figure-1.json'
        data=json.loads(scene.read_text());node=next(n for n in data['nodes'] if n['shape']=='image')
        asset=scene.parent/node['asset'];asset.write_bytes(asset.read_bytes()+b'\n')
        with self.assertRaises(ValidationError):refresh_output(self.root)


class PublishedOutputIntegrityTests(unittest.TestCase):
    def test_every_published_bundle_binds_current_source_and_qa(self):
        from paper_figure.outputs import read_paper
        for metadata in (ROOT/'output').glob('*/sources.json'):
            with self.subTest(paper=metadata.parent.name): read_paper(metadata.parent, ROOT)

    def test_every_published_local_link_resolves(self):
        for path in (ROOT/'output').rglob('*'):
            if path.suffix=='.html':
                parser=Links();parser.feed(path.read_text());links=parser.links
            elif path.suffix=='.md':links=re.findall(r'\]\(([^)]+)\)',path.read_text())
            else:continue
            for link in links:
                parsed=urlsplit(link)
                if not parsed.scheme and parsed.path:
                    self.assertTrue((path.parent/unquote(parsed.path)).resolve().is_file(),(path,link))
