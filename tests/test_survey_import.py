import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from paper_figure.model import ValidationError
from paper_figure.queue import initialize_queue, read_checkpoint, update_checkpoint

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('import_survey', ROOT / 'research/import_survey.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SurveyImportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'data').mkdir()
        rows = [{'id': 'test-paper', 'title': 'Test: Paper', 'status': 'not_reviewed', 'notes': ''},
                {'id': 'old-paper', 'title': 'Old Paper', 'status': 'recreated', 'notes': 'Existing recreation; QA pending.'}]
        (self.root / 'data/catalog.json').write_text(json.dumps({'papers': rows}))
        initialize_queue(self.root)
        self.pdf = self.root / 'build/sources/test.pdf'
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b'%PDF-1.7\nfixture source')
        self.survey_path = self.root / 'research/survey/test-paper.json'
        self.survey_path.parent.mkdir(parents=True)
        self.survey = {
            'catalog_id': 'test-paper', 'title_expected': 'Test: Paper',
            'source_url': 'https://example.org/test-paper', 'pdf_path': 'build/sources/test.pdf',
            'pdf_sha256': hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
            'pdf_title_observed': 'Test Paper', 'title_match': True, 'identity_reviewed': True, 'version': 'v1', 'page_count': 3,
            'source_status': 'accessible', 'figure_candidates': [], 'review_notes': 'PDF title and pages inspected.'}
        self.save()

    def save(self):
        self.survey_path.write_text(json.dumps(self.survey))

    def import_one(self):
        self.save()
        return MODULE.import_survey(self.root, self.survey_path)

    def durable(self):
        target = self.root / 'output/test-paper/paper.pdf'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.pdf.read_bytes())
        self.survey['pdf_path'] = 'output/test-paper/paper.pdf'

    def no_figure(self):
        self.survey.update({'evidence_status': 'no_method_figure',
            'no_method_figure_scope': 'All figures are result plots; no method diagram found.',
            'visual_scan_coverage': {'pages_scanned_1_based': [1, 2, 3], 'page_count': 3,
                                     'contact_sheet_inspected': True}})

    def evidence(self):
        return {'summary': 'Existing evidence', 'references': ['https://example.org/paper']}

    def test_cache_sources_are_reported_not_completed(self):
        result = self.import_one()
        self.assertEqual(result['action'], 'updated')
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['status'], 'in_progress')
        self.assertEqual(record['stages']['source_identity']['status'], 'passed')
        access = record['stages']['source_access']
        self.assertEqual(access['status'], 'reported')
        self.assertTrue(access['evidence']['observed_source']['verified_locally'])
        self.assertNotIn('source', access['evidence'])
        self.assertEqual(access['evidence']['survey']['path'], 'research/survey/test-paper.json')
        self.assertEqual(access['evidence']['survey']['sha256'], hashlib.sha256(self.survey_path.read_bytes()).hexdigest())
        for name in ('recreation', 'qa', 'published'):
            self.assertEqual(record['stages'][name]['status'], 'pending')

    def test_tmp_pdf_verified_but_never_durable(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'paper.pdf'
            path.write_bytes(self.pdf.read_bytes())
            self.survey['pdf_path'] = str(path)
            self.import_one()
        access = read_checkpoint(self.root, 'test-paper')['stages']['source_access']
        self.assertEqual(access['status'], 'reported')
        self.assertFalse(access['evidence']['observed_source']['durable'])

    def test_verified_durable_source_promotes_access_only(self):
        self.durable()
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper', verify_files=True)
        self.assertEqual(record['stages']['source_access']['status'], 'passed')
        self.assertEqual(record['status'], 'in_progress')
        self.assertEqual(record['stages']['published']['status'], 'pending')

    def test_idempotence_and_changed_survey_history(self):
        self.import_one()
        path = self.root / 'data/queue/test-paper.json'
        before = path.read_bytes()
        self.assertEqual(self.import_one()['action'], 'unchanged')
        self.assertEqual(before, path.read_bytes())
        self.survey['review_notes'] = 'Another specific observed detail.'
        self.assertEqual(self.import_one()['action'], 'updated')
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['revision'], 3)
        self.assertEqual(record['history'][-1]['actor'], 'survey-import')

    def test_missing_pdf_retains_reported_claim_only(self):
        self.pdf.unlink()
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['stages']['source_identity']['status'], 'reported')
        self.assertEqual(record['stages']['source_access']['status'], 'reported')
        self.assertEqual(record['status'], 'in_progress')

    def test_corrupt_source_and_wrong_hash_fail_without_mutation(self):
        checkpoint = self.root / 'data/queue/test-paper.json'
        before = checkpoint.read_bytes()
        self.survey['pdf_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValidationError, 'hash mismatch'):
            self.import_one()
        self.assertEqual(checkpoint.read_bytes(), before)
        self.pdf.write_bytes(b'<html>error</html>')
        self.survey['pdf_sha256'] = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValidationError, 'PDF bytes'):
            self.import_one()
        self.assertEqual(checkpoint.read_bytes(), before)

    def test_wrong_catalog_title_rejected(self):
        self.survey['title_expected'] = 'An unrelated source'
        with self.assertRaisesRegex(ValidationError, 'catalog checkpoint'):
            self.import_one()

    def test_claimed_match_with_different_observed_title_remains_reported(self):
        self.survey.pop('identity_reviewed')
        self.survey['pdf_title_observed'] = 'A different paper'
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['stages']['source_identity']['status'], 'reported')
        self.assertEqual(record['status'], 'in_progress')

    def test_source_mismatch_has_explicit_title_and_hash_evidence(self):
        self.survey['title_match'] = False
        self.survey['pdf_title_observed'] = 'An unrelated source'
        self.survey['source_status'] = 'source_mismatch'
        self.survey['mismatch_reason'] = 'First-page visual review confirms an unrelated title and authors.'
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['status'], 'source_mismatch')
        self.assertEqual(record['stages']['source_identity']['status'], 'failed')
        self.assertTrue(record['terminal_evidence']['observed_source']['verified_locally'])

    def test_machine_false_title_is_reported_not_terminal(self):
        self.survey.pop('identity_reviewed')
        self.survey.update(title_match=False, pdf_title_observed='A machine-parsed different title',
                           source_status='source_mismatch', mismatch_reason='Automatic title string differs.',
                           review_notes='Title machine-matched; pixels not inspected.')
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['status'], 'in_progress')
        self.assertEqual(record['stages']['source_identity']['status'], 'reported')
        self.assertIsNone(record['terminal_evidence'])

    def test_machine_true_title_without_visual_review_is_only_reported(self):
        self.survey.pop('identity_reviewed')
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['stages']['source_identity']['status'], 'reported')

    def test_manual_first_page_method_accepts_reviewed_match(self):
        self.survey.pop('identity_reviewed')
        self.survey['title_review_method'] = 'manual_first_page'
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['stages']['source_identity']['status'], 'passed')

    def test_explicit_identity_review_accepts_confirmed_catalog_title_variant(self):
        self.survey['pdf_title_observed'] = 'Paper: Test'
        self.import_one()
        identity = read_checkpoint(self.root, 'test-paper')['stages']['source_identity']
        self.assertEqual(identity['status'], 'passed')
        self.assertEqual(identity['evidence']['observed_title'], 'Paper: Test')

    def test_visual_source_candidates_are_sufficient_for_existing_matched_surveys(self):
        self.survey.pop('identity_reviewed')
        self.survey['figure_candidates'] = [{'figure': 'Figure 1', 'visually_inspected': True}]
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['stages']['source_identity']['status'], 'passed')

    def test_mismatch_requires_reason_even_after_manual_review(self):
        self.survey.update(title_match=False, pdf_title_observed='A different paper')
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['stages']['source_identity']['status'], 'reported')

    def test_visual_candidates_alone_cannot_certify_a_title_mismatch(self):
        self.survey.pop('identity_reviewed')
        self.survey.update(title_match=False, pdf_title_observed='Different title', mismatch_reason='Observed title differs.',
                           figure_candidates=[{'figure': 'Figure 1', 'visually_inspected': True}])
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')

    def test_legacy_machine_terminal_is_reopened_with_history_preserved(self):
        evidence = {**self.evidence(), 'survey_import': True}
        update_checkpoint(self.root, 'test-paper', {'status': 'source_mismatch', 'terminal_evidence': evidence,
                          'stages': {'source_identity': {'status': 'failed', 'evidence': evidence}}})
        self.survey.pop('identity_reviewed')
        self.survey.update(title_match=False, pdf_title_observed='Machine parsed title')
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['status'], 'in_progress')
        self.assertEqual(record['stages']['source_identity']['status'], 'reported')
        self.assertIsNone(record['terminal_evidence'])
        self.assertEqual(record['history'][1]['patch']['status'], 'source_mismatch')

    def test_legacy_machine_pass_is_downgraded_without_visual_evidence(self):
        evidence = {**self.evidence(), 'survey_import': True, 'matches_catalog': True,
                    'observed_title': 'Test Paper', 'source_url': self.survey['source_url'],
                    'source_sha256': self.survey['pdf_sha256']}
        update_checkpoint(self.root, 'test-paper', {'status': 'in_progress',
                          'stages': {'source_identity': {'status': 'passed', 'evidence': evidence}}})
        self.survey.pop('identity_reviewed')
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['stages']['source_identity']['status'], 'reported')

    def test_mismatch_without_local_source_is_not_terminal(self):
        self.pdf.unlink()
        self.survey.update(title_match=False, pdf_title_observed='A different paper', source_status='source_mismatch')
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')

    def test_inaccessible_requires_explicit_disposition_and_reason(self):
        self.pdf.unlink()
        self.survey['source_status'] = 'inaccessible'
        self.survey['review_notes'] = ''
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')
        self.survey['review_notes'] = 'Official URL returns 404 and checked alternate official source is unavailable.'
        self.survey['http_status'] = 404
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['status'], 'inaccessible')
        self.assertEqual(record['stages']['source_access']['status'], 'failed')

    def test_temporary_error_does_not_imply_inaccessible(self):
        self.pdf.unlink()
        self.survey.update(source_status='error', review_notes='HTTP 503, retry needed.')
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')

    def test_empty_candidates_alone_never_mean_no_suitable_figure(self):
        self.durable()
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['status'], 'in_progress')
        self.assertEqual(record['stages']['figure_selection']['status'], 'pending')

    def test_no_figure_needs_full_coverage_scope_and_durable_source(self):
        self.no_figure()
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')
        self.durable()
        self.survey['visual_scan_coverage']['pages_scanned_1_based'] = [1, 2]
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')
        self.survey['visual_scan_coverage']['pages_scanned_1_based'] = [1, 2, 3]
        self.survey['no_method_figure_scope'] = ''
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')
        self.survey['no_method_figure_scope'] = 'All full-source figures are result plots; no method diagram found.'
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper', verify_files=True)
        self.assertEqual(record['status'], 'no_suitable_figure')
        self.assertEqual(record['stages']['figure_selection']['evidence']['reviewed_pages'], [1, 2, 3])

    def test_uninspected_coverage_does_not_make_terminal(self):
        self.no_figure()
        self.durable()
        self.survey['visual_scan_coverage']['contact_sheet_inspected'] = False
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')

    def test_candidates_are_preserved_as_candidates_not_selected(self):
        self.durable()
        self.survey['figure_candidates'] = [{'figure': 'Figure 1', 'page_1_based': 2, 'visually_inspected': True}]
        self.import_one()
        stage = read_checkpoint(self.root, 'test-paper')['stages']['figure_selection']
        self.assertEqual(stage['status'], 'reported')
        self.assertEqual(stage['evidence']['figure_candidates'], self.survey['figure_candidates'])

    def test_conflicting_no_method_and_candidates_not_terminal(self):
        self.no_figure()
        self.durable()
        self.survey['figure_candidates'] = [{'figure': 'Figure 1', 'page_1_based': 2}]
        self.import_one()
        self.assertEqual(read_checkpoint(self.root, 'test-paper')['status'], 'in_progress')

    def test_existing_recreation_is_preserved(self):
        self.survey.update(catalog_id='old-paper', title_expected='Old Paper', pdf_title_observed='Old Paper')
        previous = read_checkpoint(self.root, 'old-paper')
        self.import_one()
        current = read_checkpoint(self.root, 'old-paper')
        self.assertEqual(current['status'], 'recreated')
        for name in ('recreation', 'qa', 'published'):
            self.assertEqual(previous['stages'][name], current['stages'][name])

    def test_active_downstream_work_not_overwritten(self):
        update_checkpoint(self.root, 'test-paper', {'status': 'in_progress', 'stages': {
            'recreation': {'status': 'in_progress', 'evidence': self.evidence()}}})
        before = read_checkpoint(self.root, 'test-paper')
        result = self.import_one()
        self.assertEqual(result['reason'], 'preserved_active_downstream_work')
        self.assertEqual(before, read_checkpoint(self.root, 'test-paper'))

    def test_terminal_decision_not_overwritten(self):
        update_checkpoint(self.root, 'test-paper', {'status': 'blocked', 'terminal_evidence': self.evidence()})
        before = read_checkpoint(self.root, 'test-paper')
        result = self.import_one()
        self.assertEqual(result['reason'], 'preserved_terminal_decision')
        self.assertEqual(before, read_checkpoint(self.root, 'test-paper'))

    def test_non_survey_config_is_skipped(self):
        self.survey = {'id': 'test-figure-1', 'figure': 'Figure 1', 'crop': [1, 2, 3, 4]}
        self.assertEqual(self.import_one()['reason'], 'not_a_source_survey')

    def test_schema_aliases_and_versioned_url(self):
        self.survey['catalog_title'] = self.survey.pop('title_expected')
        self.survey['pdf_local_path'] = self.survey.pop('pdf_path')
        self.survey['versioned_pdf_url'] = 'https://example.org/paper-v2.pdf'
        self.import_one()
        record = read_checkpoint(self.root, 'test-paper')
        self.assertEqual(record['stages']['source_identity']['status'], 'passed')
        self.assertEqual(record['stages']['source_identity']['evidence']['source_url'], self.survey['versioned_pdf_url'])

    def test_verified_source_conflict_does_not_overwrite_existing(self):
        self.durable()
        self.import_one()
        before = read_checkpoint(self.root, 'test-paper')
        self.pdf.write_bytes(b'%PDF-1.7\nA different version')
        self.survey['pdf_path'] = 'build/sources/test.pdf'
        self.survey['pdf_sha256'] = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        result = self.import_one()
        self.assertEqual(result['reason'], 'source_conflicts_with_verified_checkpoint')
        self.assertEqual(before, read_checkpoint(self.root, 'test-paper'))

    def test_dry_run_does_not_mutate(self):
        before = read_checkpoint(self.root, 'test-paper')
        result = MODULE.import_survey(self.root, self.survey_path, dry_run=True)
        self.assertEqual(result['action'], 'would_update')
        self.assertEqual(before, read_checkpoint(self.root, 'test-paper'))

    def test_pdf_outside_allowed_source_areas_is_rejected(self):
        self.survey['pdf_path'] = '/etc/example.pdf'
        with self.assertRaisesRegex(ValidationError, 'repository or /tmp'):
            self.import_one()

    def test_cli_collects_per_file_errors_and_continues(self):
        invalid = self.survey_path.parent / 'invalid.json'
        invalid.write_text('{invalid')
        command = [sys.executable, str(ROOT / 'research/import_survey.py'), '--repository', str(self.root)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['counts']['updated'], 1)
        self.assertEqual(output['counts']['error'], 1)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
