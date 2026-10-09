import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

try:
    import fitz
except ImportError:
    fitz = None

from paper_figure.model import ValidationError
from paper_figure.queue import initialize_queue, read_checkpoint, update_checkpoint

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('package_dispositions', ROOT / 'research/package_dispositions.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(fitz, 'optional PyMuPDF dependency unavailable')
class DispositionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'data').mkdir()
        (self.root / 'data/catalog.json').write_text(json.dumps({'papers': [
            {'id': 'test-paper', 'title': 'Test Paper', 'status': 'not_reviewed', 'notes': ''}]}))
        initialize_queue(self.root)
        self.pdf = self.root / 'build/sources/test.pdf'
        self.pdf.parent.mkdir(parents=True)
        self.make_pdf()
        self.survey_path = self.root / 'research/survey/test-paper.json'
        self.survey_path.parent.mkdir(parents=True)
        self.survey = {
            'catalog_id': 'test-paper', 'title_expected': 'Test Paper', 'pdf_title_observed': 'Test Paper',
            'title_match': True, 'source_status': 'accessible', 'evidence_status': 'no_method_figure',
            'pdf_path': 'build/sources/test.pdf', 'pdf_sha256': self.hash(self.pdf), 'page_count': 3,
            'version': '2401.12345v2', 'versioned_pdf_url': 'https://arxiv.org/pdf/2401.12345v2',
            'figure_candidates': [], 'review_notes': 'All pages visually inspected: only experiment/result plots.',
            'no_method_figure_scope': 'No architecture or algorithm-process diagram found; mathematical figures exist.',
            'visual_scan_coverage': {'page_count': 3, 'pages_scanned_1_based': [1, 2, 3], 'contact_sheet_inspected': True},
            'inspected_at': '2026-10-09', 'license_note': 'Test fixture only.'}
        self.save()
        self.output = self.root / 'output/test-paper'

    def hash(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def make_pdf(self, title='Test Paper', version='2401.12345v2', pages=3):
        document = fitz.open()
        for number in range(pages):
            page = document.new_page()
            page.insert_text((50, 50), title if number == 0 else f'Results page {number + 1}')
            if number == 0:
                page.insert_text((50, 80), 'arXiv:' + version)
        document.save(self.pdf)
        document.close()

    def save(self):
        self.survey_path.write_text(json.dumps(self.survey))

    def package(self, apply=True):
        self.save()
        return MODULE.package_disposition(self.root, self.survey_path, apply=apply)

    def test_source_only_bundle_has_exact_pdf_and_scoped_explanation(self):
        result = self.package()
        self.assertEqual(result['action'], 'created')
        self.assertEqual(result['editable_deliverable_count'], 0)
        self.assertEqual({path.name for path in self.output.iterdir()},
                         {'paper-2401.12345v2.pdf', 'README.md', 'disposition.json'})
        self.assertEqual((self.output / 'paper-2401.12345v2.pdf').read_bytes(), self.pdf.read_bytes())
        data = json.loads((self.output / 'disposition.json').read_text())
        self.assertEqual(data['status'], 'no_suitable_figure')
        self.assertEqual(data['delivery_kind'], 'source_only_disposition')
        self.assertEqual(data['reviewed_pages'], [1, 2, 3])
        self.assertEqual(data['source_sha256'], self.hash(self.pdf))
        self.assertIn('does not claim that the paper has no illustrations', (self.output / 'README.md').read_text())
        self.assertFalse((self.output / 'sources.json').exists())

    def test_dry_run_has_no_filesystem_mutations(self):
        before = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        result = MODULE.package_disposition(self.root, self.survey_path)
        self.assertEqual(result['action'], 'planned')
        self.assertFalse(result['applied'])
        after = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.root / 'output').exists())

    def test_queue_catalog_and_survey_are_never_modified(self):
        sources = [self.root / 'data/catalog.json', self.root / 'data/queue/test-paper.json', self.survey_path]
        before = {path: path.read_bytes() for path in sources}
        result = self.package()
        self.assertEqual(before, {path: path.read_bytes() for path in sources})
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'not_reviewed')
        self.assertEqual(result['survey_patch'], {'pdf_path': 'output/test-paper/paper-2401.12345v2.pdf'})

    def test_returned_queue_patch_is_valid_after_publication(self):
        result = self.package()
        record = update_checkpoint(self.root, 'test-paper', result['queue_patch'], expected_revision=1)
        self.assertEqual(record['status'], 'no_suitable_figure')
        self.assertEqual(read_checkpoint(self.root, 'test-paper', verify_files=True)['status'], 'no_suitable_figure')
        for name in ('recreation', 'qa', 'published'):
            self.assertEqual(record['stages'][name]['status'], 'pending')

    def test_idempotent_byte_preserving_republication(self):
        self.package()
        before = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.assertEqual(self.package()['action'], 'unchanged')
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.output.iterdir()})

    def test_idempotent_after_caller_updates_survey_pdf_location(self):
        initial = self.package()
        before = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.survey.update(initial['survey_patch'])
        result = self.package()
        self.assertEqual(result['action'], 'unchanged')
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.output.iterdir()})
        self.assertEqual(result['disposition'], json.loads((self.output / 'disposition.json').read_text()))

    def test_empty_candidates_alone_are_insufficient(self):
        self.survey.pop('evidence_status')
        with self.assertRaisesRegex(ValidationError, 'Explicit no_method_figure'):
            self.package()
        self.assertFalse(self.output.exists())

    def test_candidate_figure_conflict_rejected(self):
        self.survey['figure_candidates'] = [{'figure': 'Figure 1'}]
        with self.assertRaises(ValidationError):
            self.package()
        self.assertFalse(self.output.exists())

    def test_full_visual_coverage_and_reason_required(self):
        original = copy.deepcopy(self.survey)
        for change in ('missing_page', 'not_inspected', 'wrong_count', 'no_scope', 'no_reason', 'boolean_page'):
            self.survey = copy.deepcopy(original)
            if change == 'missing_page':
                self.survey['visual_scan_coverage']['pages_scanned_1_based'] = [1, 2]
            elif change == 'not_inspected':
                self.survey['visual_scan_coverage']['contact_sheet_inspected'] = False
            elif change == 'wrong_count':
                self.survey['visual_scan_coverage']['page_count'] = 4
            elif change == 'no_scope':
                self.survey['no_method_figure_scope'] = ''
            elif change == 'no_reason':
                self.survey['review_notes'] = ''
            else:
                self.survey['visual_scan_coverage']['pages_scanned_1_based'] = [True, 2, 3]
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.package()
            self.assertFalse(self.output.exists())

    def test_version_record_and_fixed_official_url_required(self):
        original = copy.deepcopy(self.survey)
        for version, url in [('2401.12345', 'https://arxiv.org/pdf/2401.12345'),
                             ('2401.12345v2', 'https://arxiv.org/pdf/2401.12345'),
                             ('2401.12345v2', 'https://evil.example/pdf/2401.12345v2'),
                             ('2401.12345v2', 'https://arxiv.org/pdf/2401.12345v1'),
                             ('2401.12345v2', 'https://arxiv.org/pdf/2401.12345v2?download=1')]:
            self.survey = copy.deepcopy(original)
            self.survey.update(version=version, versioned_pdf_url=url)
            with self.subTest(version=version, url=url), self.assertRaises(ValidationError):
                self.package()
            self.assertFalse(self.output.exists())

    def test_actual_pdf_page_count_is_verified(self):
        self.make_pdf(pages=2)
        self.survey['pdf_sha256'] = self.hash(self.pdf)
        with self.assertRaisesRegex(ValidationError, 'Actual PDF page count'):
            self.package()

    def test_actual_first_page_version_is_verified(self):
        self.make_pdf(version='2401.12345v1')
        self.survey['pdf_sha256'] = self.hash(self.pdf)
        with self.assertRaisesRegex(ValidationError, 'Fixed version not verified'):
            self.package()

    def test_actual_first_page_title_is_verified(self):
        self.make_pdf(title='Another unrelated paper')
        self.survey['pdf_sha256'] = self.hash(self.pdf)
        with self.assertRaisesRegex(ValidationError, 'Observed title not verified'):
            self.package()

    def test_machine_or_recorded_title_mismatch_rejected(self):
        self.survey['title_match'] = False
        with self.assertRaisesRegex(ValidationError, 'Reviewed source title'):
            self.package()

    def test_pdf_hash_and_signature_are_verified(self):
        self.survey['pdf_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValidationError, 'hash mismatch'):
            self.package()
        self.pdf.write_bytes(b'<html>rate limited</html>')
        self.survey['pdf_sha256'] = self.hash(self.pdf)
        with self.assertRaisesRegex(ValidationError, 'PDF bytes'):
            self.package()

    def test_header_only_fake_pdf_is_rejected(self):
        self.pdf.write_bytes(b'%PDF-1.7\nnot a parsed PDF')
        self.survey['pdf_sha256'] = self.hash(self.pdf)
        with self.assertRaises(ValidationError):
            self.package()

    def test_safe_ids_and_catalog_identity_checked_before_publication(self):
        for paper_id in ('../escape', 'UPPER', 'unknown-paper'):
            self.survey['catalog_id'] = paper_id
            with self.subTest(paper_id=paper_id), self.assertRaises(ValidationError):
                self.package()
        self.assertFalse((self.root / 'output').exists())

    def test_existing_editable_folder_never_overwritten(self):
        self.output.mkdir(parents=True)
        (self.output / 'sources.json').write_text('{"existing":true}')
        (self.output / 'figure.pptx').write_bytes(b'original editable content')
        before = {path.name: path.read_bytes() for path in self.output.iterdir()}
        with self.assertRaisesRegex(ValidationError, 'existing editable'):
            self.package()
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.output.iterdir()})

    def test_changed_review_cannot_overwrite_existing_disposition(self):
        self.package()
        before = (self.output / 'disposition.json').read_bytes()
        self.survey['review_notes'] = 'A changed scope/review conclusion.'
        with self.assertRaisesRegex(ValidationError, 'evidence differs'):
            self.package()
        self.assertEqual(before, (self.output / 'disposition.json').read_bytes())

    def test_existing_source_tamper_rejected(self):
        self.package()
        (self.output / 'paper-2401.12345v2.pdf').write_bytes(b'changed source bytes')
        with self.assertRaisesRegex(ValidationError, 'Existing source PDF hash'):
            self.package()

    def test_failed_copy_or_rename_leaves_no_partial_bundle(self):
        for target in ('shutil.copyfile', 'os.rename'):
            with self.subTest(target=target), patch.object(
                    MODULE.shutil if target.startswith('shutil') else MODULE.os,
                    target.split('.')[1], side_effect=OSError('injected failure')):
                with self.assertRaises(OSError):
                    self.package()
            self.assertFalse(self.output.exists())
            self.assertFalse(list((self.root / 'output').glob('.disposition-*')))

    def test_source_modified_during_copy_is_not_published(self):
        def corrupt(source, destination):
            Path(destination).write_bytes(b'%PDF-1.7 changed during copy')
        with patch.object(MODULE.shutil, 'copyfile', side_effect=corrupt):
            with self.assertRaisesRegex(ValidationError, 'Staged source hash'):
                self.package()
        self.assertFalse(self.output.exists())

    def test_parallel_same_paper_publication_is_idempotent(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: MODULE.package_disposition(self.root, self.survey_path, apply=True), range(4)))
        self.assertEqual(sum(result['action'] == 'created' for result in results), 1)
        self.assertEqual(sum(result['action'] == 'unchanged' for result in results), 3)

    def test_output_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as external:
            (self.root / 'output').symlink_to(external, target_is_directory=True)
            with self.assertRaises(ValidationError):
                self.package()
            self.assertFalse(list(Path(external).iterdir()))

    def test_cli_is_plan_by_default_and_apply_is_explicit(self):
        command = [sys.executable, str(ROOT / 'research/package_dispositions.py'), '--repository', str(self.root),
                   str(self.survey_path)]
        plan = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(plan.stdout)['results'][0]['action'], 'planned')
        self.assertFalse(self.output.exists())
        published = subprocess.run(command + ['--apply'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(published.stdout)['results'][0]['action'], 'created')


if __name__ == '__main__':
    unittest.main()
