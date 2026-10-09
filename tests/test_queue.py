import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from paper_figure.model import ValidationError
from paper_figure.queue import (STAGES, initialize_queue, queue_status, read_checkpoint,
                                read_json, safe_id, update_checkpoint)

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QueueTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'data').mkdir()
        self.catalog = self.root / 'data/catalog.json'
        self.rows = [
            {'id': 'new-paper', 'title': 'New paper', 'status': 'not_reviewed', 'notes': ''},
            {'id': 'old-paper', 'title': 'Old paper', 'status': 'recreated', 'notes': 'Existing exports; QA pending.'},
            {'id': 'held-paper', 'title': 'Held paper', 'status': 'blocked', 'notes': 'License restriction recorded.'},
        ]
        self.write_catalog(self.rows)
        initialize_queue(self.root)
        self.checkpoint = self.root / 'data/queue/new-paper.json'

    def write_catalog(self, rows):
        self.catalog.write_text(json.dumps({'source_commit': 'abc123', 'papers': rows}))

    def evidence(self, **extra):
        return {'summary': 'Checked against the source.', 'references': ['https://example.org/paper'], **extra}

    def stage(self, status='passed', **extra):
        return {'status': status, 'evidence': self.evidence(**extra)}

    def artifact(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return {'path': relative, 'sha256': digest(path)}

    def completion(self):
        source = self.artifact('output/new-paper/paper.pdf', b'%PDF-1.7\nsource fixture')
        artifacts = {
            'scene': self.artifact('data/scene.json', b'{"fixture":true}'),
            'pptx': self.artifact('output/new-paper/figure.pptx', b'fixture pptx bytes'),
            'drawio': self.artifact('output/new-paper/figure.drawio', b'<mxfile/>'),
            'preview': self.artifact('output/new-paper/figure.png', b'fixture preview bytes'),
            'original': self.artifact('output/new-paper/original.png', b'fixture original bytes'),
        }
        report = {'source_sha256': source['sha256'], 'figure': 'Figure 1', 'pdf_page': 2,
                  'artifact_sha256': {kind: ref['sha256'] for kind, ref in artifacts.items()},
                  'checks': {'source_comparison': 'passed', 'pptx_open_render': 'passed', 'drawio_open_render': 'passed'},
                  'notes': 'Test evidence fixture only; not actual application QA.', 'reviewer': 'unit-test'}
        qa = self.artifact('output/new-paper/qa.json', json.dumps(report).encode())
        stages = {
            'source_identity': self.stage(matches_catalog=True, observed_title='New paper',
                                          source_url='https://example.org/paper.pdf', source_sha256=source['sha256']),
            'source_access': self.stage(source=source, page_count=4),
            'figure_selection': self.stage(figure='Figure 1', pdf_page=2),
            'recreation': self.stage(artifacts=artifacts),
            'qa': self.stage(report=qa),
            'published': self.stage(output_directory='output/new-paper'),
        }
        return {'status': 'completed', 'terminal_evidence': self.evidence(), 'stages': stages}

    def test_import_is_honest_and_idempotent(self):
        before = {p: p.read_bytes() for p in (self.root / 'data/queue').glob('*.json')}
        result = initialize_queue(self.root)
        self.assertEqual(result, {'created': 0, 'existing': 3, 'catalog_papers': 3})
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        stats = queue_status(self.root)
        self.assertEqual(stats['status']['completed'], 0)
        self.assertEqual(stats['status']['recreated'], 1)
        record = read_checkpoint(self.root, 'old-paper')
        self.assertEqual(record['stages']['recreation']['status'], 'reported')
        self.assertEqual(record['stages']['qa']['status'], 'pending')
        self.assertTrue(record['stages']['recreation']['evidence']['imported_claim_only'])
        self.assertEqual(record['catalog']['sha256'], digest(self.catalog))

    def test_import_real_137_paper_catalog(self):
        self.catalog.write_bytes((ROOT / 'data/catalog.json').read_bytes())
        # Use a fresh repository so the three fixture IDs are not included.
        fresh = self.root / 'fresh'
        (fresh / 'data').mkdir(parents=True)
        (fresh / 'data/catalog.json').write_bytes(self.catalog.read_bytes())
        self.assertEqual(initialize_queue(fresh)['created'], 137)
        self.assertEqual({key: value for key, value in queue_status(fresh)['status'].items() if value},
                         dict(__import__('collections').Counter('in_progress' if p['status']=='no_suitable_figure' else p['status'] for p in json.loads(self.catalog.read_text())['papers'])))

    def test_import_preserves_progress_and_source_snapshot(self):
        update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'})
        self.rows[0]['notes'] = 'Later catalog edit'
        self.write_catalog(self.rows)
        initialize_queue(self.root)
        saved = read_checkpoint(self.root, 'new-paper')
        self.assertEqual(saved['status'], 'in_progress')
        self.assertEqual(saved['revision'], 2)
        self.assertEqual(saved['catalog']['paper']['notes'], '')

    def test_invalid_catalog_ids_and_duplicates_fail_before_writes(self):
        for rows in ([self.rows[0], self.rows[0]], [dict(self.rows[0], id='../escape')],
                     [dict(self.rows[0], status='completed')], [dict(self.rows[0], title=None)]):
            with self.subTest(rows=rows):
                self.write_catalog(rows)
                with self.assertRaises(ValidationError):
                    initialize_queue(self.root)
                self.assertEqual(len(list((self.root / 'data/queue').glob('*.json'))), 3)

    def test_safe_ids(self):
        for value in ('../outside', '/absolute', '.', '', 'UPPER', 'a/b', 'a\\b', 'x' * 181, None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                safe_id(value)
        self.assertEqual(safe_id('paper-123_ok'), 'paper-123_ok')

    def test_update_audit_and_revision_conflict(self):
        old_bytes = self.checkpoint.read_bytes()
        record = update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'}, 1, actor='worker-a')
        self.assertEqual(record['revision'], 2)
        self.assertEqual(record['history'][-1]['previous_sha256'], hashlib.sha256(old_bytes).hexdigest())
        self.assertEqual(record['history'][-1]['actor'], 'worker-a')
        with self.assertRaisesRegex(ValidationError, 'revision conflict'):
            update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'}, 1)
        self.assertEqual(read_checkpoint(self.root, 'new-paper')['revision'], 2)

    def test_terminal_outcomes_need_explicit_evidence(self):
        for status in ('completed', 'no_suitable_figure', 'inaccessible', 'source_mismatch', 'blocked'):
            with self.subTest(status=status), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', {'status': status})
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'new-paper', {'status': 'blocked', 'terminal_evidence': {'summary': 'why'}})
        result = update_checkpoint(self.root, 'new-paper', {'status': 'blocked', 'terminal_evidence': self.evidence()})
        self.assertEqual(result['status'], 'blocked')

    def test_failure_outcomes_require_relevant_failed_stage(self):
        for status, stage in [('inaccessible', 'source_access'), ('source_mismatch', 'source_identity')]:
            with self.subTest(status=status):
                body = {'status': status, 'terminal_evidence': self.evidence()}
                with self.assertRaises(ValidationError):
                    update_checkpoint(self.root, 'new-paper', body)
                body['stages'] = {stage: self.stage('failed')}
                self.assertEqual(update_checkpoint(self.root, 'new-paper', body)['status'], status)

    def test_no_figure_requires_source_review_and_actual_pages(self):
        body = self.completion()
        body['status'] = 'no_suitable_figure'
        body['stages'] = {key: value for key, value in body['stages'].items() if key in STAGES[:2]}
        body['stages']['figure_selection'] = self.stage('failed')
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'new-paper', body)
        body['stages']['figure_selection']['evidence']['reviewed_pages'] = [1, 5]
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'new-paper', body)
        body['stages']['figure_selection']['evidence']['reviewed_pages'] = [1, 2, 3, 4]
        self.assertEqual(update_checkpoint(self.root, 'new-paper', body)['status'], 'no_suitable_figure')

    def test_blocked_can_resume_without_losing_history(self):
        result = update_checkpoint(self.root, 'held-paper', {'status': 'in_progress'})
        self.assertIsNone(result['terminal_evidence'])
        self.assertEqual(result['catalog']['paper']['status'], 'blocked')
        self.assertEqual(len(result['history']), 2)

    def test_completed_requires_all_stages_and_exact_files(self):
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'new-paper', {'status': 'completed', 'terminal_evidence': self.evidence()})
        result = update_checkpoint(self.root, 'new-paper', self.completion())
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(queue_status(self.root, verify_files=True)['status']['completed'], 1)

    def test_invalid_completion_does_not_touch_checkpoint(self):
        body = self.completion()
        before = self.checkpoint.read_bytes()
        for modification in ('missing', 'hash', 'identity', 'page', 'qa', 'publication', 'figure'):
            candidate = copy.deepcopy(body)
            if modification == 'missing':
                candidate['stages']['recreation']['evidence']['artifacts']['pptx']['path'] = 'missing.pptx'
            elif modification == 'hash':
                candidate['stages']['source_access']['evidence']['source']['sha256'] = '0' * 64
            elif modification == 'identity':
                candidate['stages']['source_identity']['evidence']['source_sha256'] = '0' * 64
            elif modification == 'page':
                candidate['stages']['figure_selection']['evidence']['pdf_page'] = 5
            elif modification == 'qa':
                candidate['stages']['qa'] = {'status': 'pending', 'evidence': None}
            elif modification == 'publication':
                candidate['stages']['published']['evidence']['output_directory'] = 'data'
            elif modification == 'figure':
                candidate['stages']['figure_selection']['evidence']['figure'] = 'Figure 2'
            with self.subTest(modification=modification), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', candidate)
            self.assertEqual(before, self.checkpoint.read_bytes())

    def test_qa_report_must_bind_every_artifact_and_real_checks(self):
        body = self.completion()
        report_path = self.root / body['stages']['qa']['evidence']['report']['path']
        original = json.loads(report_path.read_text())
        for field in ('artifact_sha256', 'source_sha256', 'checks', 'reviewer', 'notes'):
            report = copy.deepcopy(original)
            report.pop(field)
            report_path.write_text(json.dumps(report))
            body['stages']['qa']['evidence']['report']['sha256'] = digest(report_path)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', body)

    def test_stale_artifact_detected_by_verified_status(self):
        body = self.completion()
        update_checkpoint(self.root, 'new-paper', body)
        (self.root / 'output/new-paper/figure.pptx').write_bytes(b'changed')
        self.assertEqual(queue_status(self.root)['status']['completed'], 1)
        self.assertFalse(queue_status(self.root)['files_verified'])
        with self.assertRaisesRegex(ValidationError, 'hash mismatch'):
            queue_status(self.root, verify_files=True)

    def test_identity_requires_source_hash_and_valid_url_before_access(self):
        for extra in ({'source_url': 'https://example.org/paper'},
                      {'source_url': 'https://[', 'source_sha256': 'a' * 64}):
            body = {'status': 'in_progress', 'stages': {
                'source_identity': self.stage(matches_catalog=True, observed_title='New paper', **extra)}}
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', body)

    def test_source_must_be_pdf_bytes(self):
        body = self.completion()
        ref = body['stages']['source_access']['evidence']['source']
        path = self.root / ref['path']
        path.write_bytes(b'<html>rate limited</html>')
        ref['sha256'] = digest(path)
        with self.assertRaisesRegex(ValidationError, 'PDF bytes'):
            update_checkpoint(self.root, 'new-paper', body)

    def test_recreated_and_not_reviewed_cannot_hide_unperformed_stages(self):
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'new-paper', {'status': 'recreated'})
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'old-paper', {'status': 'not_reviewed'})

    def test_stage_dependencies_and_pending_evidence(self):
        for stage in STAGES[2:]:
            with self.subTest(stage=stage), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', {'status': 'in_progress', 'stages': {stage: self.stage()}})
        with self.assertRaises(ValidationError):
            update_checkpoint(self.root, 'new-paper', {'status': 'in_progress', 'stages': {'qa': self.stage('pending')}})

    def test_immutable_fields_and_bad_types_are_rejected(self):
        for body in ({'paper_id': 'other'}, {'revision': 99}, {'history': []}, {'status': {}},
                     {'status': 'in_progress', 'stages': {'bad': {}}},
                     {'status': 'in_progress', 'stages': {'qa': {'status': [], 'evidence': None}}},
                     {'status': 'blocked', 'terminal_evidence': self.evidence(value=float('nan'))}):
            with self.subTest(body=body), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', body)

    def test_artifact_traversal_and_symlink_escape_are_rejected(self):
        body = self.completion()
        for path in ('../outside.pdf', '/tmp/outside.pdf', 'output\\outside.pdf'):
            candidate = copy.deepcopy(body)
            candidate['stages']['source_access']['evidence']['source']['path'] = path
            with self.subTest(path=path), self.assertRaises(ValidationError):
                update_checkpoint(self.root, 'new-paper', candidate)
        with tempfile.TemporaryDirectory() as outside:
            source = Path(outside) / 'paper.pdf'
            source.write_bytes(b'%PDF-1.7 outside')
            (self.root / 'escape.pdf').symlink_to(source)
            body['stages']['source_access']['evidence']['source'] = {'path': 'escape.pdf', 'sha256': digest(source)}
            with self.assertRaisesRegex(ValidationError, 'escapes repository'):
                update_checkpoint(self.root, 'new-paper', body)

    def test_checkpoint_symlink_rejected(self):
        target = self.root / 'saved.json'
        self.checkpoint.rename(target)
        self.checkpoint.symlink_to(target)
        with self.assertRaises(ValidationError):
            read_checkpoint(self.root, 'new-paper')

    def test_queue_directory_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            nested = self.root / 'nested'
            (nested / 'data').mkdir(parents=True)
            (nested / 'data/queue').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValidationError):
                queue_status(nested)

    def test_atomic_replace_failure_preserves_previous_and_cleans_temp(self):
        before = self.checkpoint.read_bytes()
        with patch('paper_figure.queue.os.replace', side_effect=OSError('injected replacement failure')):
            with self.assertRaises(OSError):
                update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'})
        self.assertEqual(before, self.checkpoint.read_bytes())
        self.assertFalse(list(self.checkpoint.parent.glob('*.tmp')))
        self.assertEqual(update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'})['revision'], 2)

    def test_parallel_writes_do_not_lose_audit_events(self):
        def work(number):
            return update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'}, actor=f'worker-{number}')
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(work, range(12)))
        self.assertEqual(sorted(result['revision'] for result in results), list(range(2, 14)))
        self.assertEqual(len(read_checkpoint(self.root, 'new-paper')['history']), 13)

    def test_parallel_optimistic_writes_allow_only_one(self):
        def work(_):
            try:
                update_checkpoint(self.root, 'new-paper', {'status': 'in_progress'}, expected_revision=1)
                return True
            except ValidationError:
                return False
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(work, range(4))), 1)

    def test_corrupt_json_duplicate_keys_and_filename_identity_fail(self):
        for data in ('{', '{"a":1,"a":2}', '{"a":NaN}'):
            self.checkpoint.write_text(data)
            with self.subTest(data=data), self.assertRaises(ValidationError):
                read_json(self.checkpoint)
        self.checkpoint.write_bytes((self.root / 'data/queue/old-paper.json').read_bytes())
        with self.assertRaisesRegex(ValidationError, 'filename'):
            queue_status(self.root)

    def test_research_entrypoint_does_not_shadow_stdlib_queue(self):
        result = subprocess.run([sys.executable, '-c',
                                 'import queue; from concurrent.futures import ThreadPoolExecutor; '
                                 'assert queue.Queue; '
                                 'pool = ThreadPoolExecutor(1); assert pool.submit(lambda: 7).result() == 7; '
                                 'pool.shutdown()'], cwd=ROOT / 'research', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cli_init_status_update_and_validation_exit(self):
        script = ROOT / 'research/queue.py'
        prefix = [sys.executable, str(script), '--repository', str(self.root)]
        init = subprocess.run(prefix + ['init'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(init.stdout)['existing'], 3)
        evidence = self.root / 'update.json'
        evidence.write_text(json.dumps({'status': 'in_progress'}))
        updated = subprocess.run(prefix + ['update', 'new-paper', str(evidence), '--expected-revision', '1'],
                                 capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(updated.stdout)['revision'], 2)
        stats = subprocess.run(prefix + ['status', '--verify-files'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(stats.stdout)['status']['in_progress'], 1)
        invalid = subprocess.run(prefix + ['update', '../outside', str(evidence)], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertNotIn('Traceback', invalid.stderr)


if __name__ == '__main__':
    unittest.main()
