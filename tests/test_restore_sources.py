import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import shutil
from research.restore_source_cache import restore
class RestoreSourcesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for p in ['data','output/demo','research/survey']:(self.root/p).mkdir(parents=True)
        source=b'%PDF-1.4\nfixture';self.hash=hashlib.sha256(source).hexdigest();(self.root/'output/demo/paper.pdf').write_bytes(source)
        (self.root/'data/catalog.json').write_text(json.dumps({'papers':[dict(id='demo-paper',output_directory='output/demo')]}))
        (self.root/'output/demo/sources.json').write_text(json.dumps({'papers':[dict(file='paper.pdf',sha256=self.hash)]}))
        (self.root/'research/survey/demo-paper.json').write_text(json.dumps(dict(pdf_sha256=self.hash,pdf_path='/tmp/old-cache.pdf')))
    def test_plan_then_restore_without_network(self):
        self.assertEqual(restore(self.root)[0]['action'],'would_restore');self.assertFalse((self.root/'build').exists())
        self.assertEqual(restore(self.root,True)[0]['action'],'restored');self.assertEqual(restore(self.root,True)[0]['action'],'already_present')
        self.assertEqual(json.loads((self.root/'research/survey/demo-paper.json').read_text())['pdf_path'],'build/sources/demo-paper.pdf')
    def test_reject_changed_archive(self):
        (self.root/'output/demo/paper.pdf').write_bytes(b'bad')
        with self.assertRaises(ValueError):restore(self.root,True)
    def test_preserve_different_existing_cache(self):
        cache=self.root/'build/sources/demo-paper.pdf';cache.parent.mkdir(parents=True);cache.write_bytes(b'old')
        with self.assertRaises(ValueError):restore(self.root,True)
        self.assertEqual(cache.read_bytes(),b'old')
    def test_reject_path_escape(self):
        (self.root/'output/demo/sources.json').write_text(json.dumps({'papers':[dict(file='../../paper.pdf',sha256=self.hash)]}))
        with self.assertRaises(ValueError):restore(self.root,True)
    def test_reject_survey_version_change(self):
        (self.root/'research/survey/demo-paper.json').write_text(json.dumps(dict(pdf_sha256='0'*64)))
        with self.assertRaises(ValueError):restore(self.root,True)
    def test_reject_survey_file_symlink_without_external_write(self):
        survey=self.root/'research/survey/demo-paper.json'
        outside=self.root/'outside-survey.json';before=survey.read_bytes();outside.write_bytes(before)
        survey.unlink();survey.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'symlink'):restore(self.root,True)
        self.assertEqual(outside.read_bytes(),before)
        self.assertFalse((self.root/'build').exists())
    def test_reject_survey_directory_symlink_without_external_write(self):
        directory=self.root/'research/survey';outside=self.root/'outside-surveys'
        directory.rename(outside);directory.symlink_to(outside,target_is_directory=True)
        before=(outside/'demo-paper.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'symlink'):restore(self.root,True)
        self.assertEqual((outside/'demo-paper.json').read_bytes(),before)
        self.assertFalse((self.root/'build').exists())
    def test_concurrent_different_cache_is_never_overwritten(self):
        target=self.root/'build/sources/demo-paper.pdf';copy=shutil.copyfile
        survey=self.root/'research/survey/demo-paper.json';before=survey.read_bytes()
        def appear_during_copy(source,destination):
            result=copy(source,destination);target.write_bytes(b'concurrent different source');return result
        with patch('research.restore_source_cache.shutil.copyfile',side_effect=appear_during_copy):
            with self.assertRaisesRegex(ValueError,'refusing overwrite'):restore(self.root,True)
        self.assertEqual(target.read_bytes(),b'concurrent different source')
        self.assertEqual(survey.read_bytes(),before)
        self.assertFalse(list(target.parent.glob('.restore-*')))
    def test_concurrent_identical_cache_is_accepted_without_replace(self):
        target=self.root/'build/sources/demo-paper.pdf';copy=shutil.copyfile
        def appear_during_copy(source,destination):
            result=copy(source,destination);copy(source,target);return result
        with patch('research.restore_source_cache.shutil.copyfile',side_effect=appear_during_copy):
            self.assertEqual(restore(self.root,True)[0]['action'],'already_present')
        self.assertEqual(target.read_bytes(),b'%PDF-1.4\nfixture')
        self.assertFalse(list(target.parent.glob('.restore-*')))
