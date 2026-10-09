"""Evidence-gated, atomic per-paper checkpoints. No download or export side effects."""
import copy
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .model import ValidationError, require

STAGES = ('source_identity', 'source_access', 'figure_selection', 'recreation', 'qa', 'published')
STAGE_STATUSES = {'pending', 'reported', 'in_progress', 'passed', 'failed', 'blocked'}
TERMINAL_STATUSES = {'completed', 'no_suitable_figure', 'inaccessible', 'source_mismatch', 'blocked'}
STATUSES = {'not_reviewed', 'in_progress', 'recreated'} | TERMINAL_STATUSES
QA_CHECKS = ('source_comparison', 'pptx_open_render', 'drawio_open_render')


def _text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f'{label}: nonempty text required')


def safe_id(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,179}', value),
            'Paper id must be a lowercase safe slug (maximum 180 characters)')
    return value


def _now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _bytes(value):
    try:
        return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise ValidationError(f'Invalid JSON value: {exc}') from exc


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'Duplicate JSON key: {key}')
            result[key] = value
        return result

    def bad_constant(value):
        raise ValidationError(f'Invalid JSON constant: {value}')

    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                          parse_constant=bad_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f'{path}: {exc}') from exc


def _inside(root, relative, directory=False):
    _text(relative, 'Repository-relative path')
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in relative,
            'Paths must be repository-relative and cannot contain traversal')
    target = (root / path).resolve()
    require(target.is_relative_to(root), 'Path escapes repository')
    require(target.is_dir() if directory else target.is_file(), f'Missing path: {relative}')
    return target


def _file_ref(root, reference):
    require(isinstance(reference, dict), 'File evidence must contain path and sha256')
    path = _inside(root, reference.get('path'))
    digest = reference.get('sha256')
    require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'Invalid SHA256')
    require(_sha(path) == digest, f'File evidence hash mismatch: {reference["path"]}')
    require(path.stat().st_size > 0, f'Empty evidence file: {reference["path"]}')
    return path


def _evidence(value):
    require(isinstance(value, dict), 'Evidence object required')
    _text(value.get('summary'), 'Evidence summary')
    refs = value.get('references')
    require(isinstance(refs, list) and refs, 'Evidence references required')
    for ref in refs:
        _text(ref, 'Evidence reference')


def _queue_dir(root, create=False):
    folder = root / 'data' / 'queue'
    require(folder.resolve().is_relative_to(root), 'Queue directory escapes repository')
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def _checkpoint_path(root, paper_id, create=False):
    path = _queue_dir(root, create) / (safe_id(paper_id) + '.json')
    require(not path.is_symlink(), 'Checkpoint cannot be a symlink')
    return path


@contextmanager
def _lock(root, paper_id):
    # POSIX advisory locks release on process exit; no stale lease to reclaim.
    import fcntl
    folder = _queue_dir(root, True) / '.locks'
    require(not folder.is_symlink(), 'Lock directory cannot be a symlink')
    folder.mkdir(exist_ok=True)
    path = folder / (safe_id(paper_id) + '.lock')
    fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _atomic_write(path, value):
    payload = _bytes(value)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.stem + '-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _validate(root, record, verify_files=False):
    require(isinstance(record, dict) and type(record.get('schema_version')) is int and record['schema_version'] == 1, 'Checkpoint schema_version must be 1')
    safe_id(record.get('paper_id'))
    require(isinstance(record.get('status'), str) and record['status'] in STATUSES, 'Invalid checkpoint status')
    require(type(record.get('revision')) is int and record['revision'] >= 1, 'Invalid revision')
    require(isinstance(record.get('catalog'), dict), 'Catalog provenance required')
    require(isinstance(record['catalog'].get('paper'), dict) and
            record['catalog']['paper'].get('id') == record['paper_id'], 'Catalog identity differs')
    stages = record.get('stages')
    require(isinstance(stages, dict) and set(stages) == set(STAGES), 'Exactly six stages required')
    for name, stage in stages.items():
        require(isinstance(stage, dict) and set(stage) == {'status', 'evidence'}, f'Invalid stage: {name}')
        require(isinstance(stage['status'], str) and stage['status'] in STAGE_STATUSES, f'Invalid stage status: {name}')
        if stage['status'] != 'pending':
            _evidence(stage['evidence'])
        else:
            require(stage['evidence'] is None, f'Pending {name} cannot claim evidence')
    history = record.get('history')
    require(isinstance(history, list) and len(history) == record['revision'], 'History/revision mismatch')
    for number, event in enumerate(history, 1):
        require(isinstance(event, dict) and event.get('revision') == number, 'Invalid audit revision')
        for key in ('at', 'actor', 'event'):
            _text(event.get(key), 'Audit ' + key)
    for name in STAGES[2:]:
        if stages[name]['status'] == 'passed':
            predecessors = STAGES[:2] if name == 'figure_selection' else (STAGES[STAGES.index(name) - 1],)
            require(all(stages[before]['status'] == 'passed' for before in predecessors),
                    f'{name}: preceding stages must pass first')
    if record['status'] in TERMINAL_STATUSES:
        _evidence(record.get('terminal_evidence'))
    else:
        require(record.get('terminal_evidence') is None, 'Nonterminal status cannot retain terminal evidence')
    if record['status'] == 'recreated':
        require(stages['recreation']['status'] in {'reported', 'passed'}, 'recreated requires reported or passed recreation')
    if record['status'] == 'not_reviewed':
        require(all(stage['status'] == 'pending' for stage in stages.values()), 'not_reviewed requires all stages pending')
    if record['status'] == 'completed':
        require(all(stage['status'] == 'passed' for stage in stages.values()), 'completed requires all six stages passed')
    if record['status'] == 'source_mismatch':
        require(stages['source_identity']['status'] == 'failed', 'source_mismatch requires failed identity check')
    if record['status'] == 'inaccessible':
        require(stages['source_access']['status'] in {'failed', 'blocked'}, 'inaccessible requires failed/blocked access')
    if record['status'] == 'no_suitable_figure':
        require(all(stages[key]['status'] == 'passed' for key in STAGES[:2]), 'Figure review requires verified accessible source')
        require(stages['figure_selection']['status'] == 'failed', 'no_suitable_figure requires a failed selection')
        pages = stages['figure_selection']['evidence'].get('reviewed_pages')
        require(isinstance(pages, list) and pages and all(type(page) is int and page > 0 for page in pages),
                'no_suitable_figure requires explicit reviewed_pages')
    if not verify_files:
        return
    identity = stages['source_identity']
    access = stages['source_access']
    if identity['status'] == 'passed':
        evidence = identity['evidence']
        require(evidence.get('matches_catalog') is True, 'Identity requires explicit matches_catalog: true')
        _text(evidence.get('observed_title'), 'Observed source title')
        url = evidence.get('source_url')
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
            valid_url = parsed and parsed.scheme in {'http', 'https'} and parsed.netloc
        except ValueError:
            valid_url = False
        require(valid_url, 'Identity requires source_url')
        source_hash = evidence.get('source_sha256')
        require(isinstance(source_hash, str) and re.fullmatch('[0-9a-f]{64}', source_hash),
                'Identity requires source_sha256')
    if access['status'] == 'passed':
        pdf = _file_ref(root, access['evidence'].get('source'))
        with pdf.open('rb') as stream:
            require(stream.read(5) == b'%PDF-', 'Source must be PDF bytes')
        require(type(access['evidence'].get('page_count')) is int and access['evidence']['page_count'] > 0,
                'Source access requires page_count')
    if identity['status'] == access['status'] == 'passed':
        require(identity['evidence'].get('source_sha256') == access['evidence']['source']['sha256'],
                'Identity must reference the exact verified source SHA256')
    selection = stages['figure_selection']
    if selection['status'] == 'passed':
        _text(selection['evidence'].get('figure'), 'Selected figure')
        page = selection['evidence'].get('pdf_page')
        require(type(page) is int and 1 <= page <= access['evidence']['page_count'], 'Invalid selected PDF page')
    if record['status'] == 'no_suitable_figure':
        require(all(page <= access['evidence']['page_count'] for page in selection['evidence']['reviewed_pages']),
                'Reviewed page outside source PDF')
    recreation = stages['recreation']
    artifacts = {}
    if recreation['status'] == 'passed':
        artifacts = recreation['evidence'].get('artifacts')
        require(isinstance(artifacts, dict) and set(artifacts) == {'scene', 'pptx', 'drawio', 'preview', 'original'},
                'Recreation requires scene, pptx, drawio, preview and original artifact references')
        suffixes = {'scene': '.json', 'pptx': '.pptx', 'drawio': '.drawio', 'preview': '.png', 'original': '.png'}
        for kind, reference in artifacts.items():
            require(_file_ref(root, reference).suffix.lower() == suffixes[kind], f'Wrong artifact suffix: {kind}')
        require(len({value['path'] for value in artifacts.values()}) == len(artifacts), 'Artifact paths must be distinct')
    if stages['qa']['status'] == 'passed':
        report = read_json(_file_ref(root, stages['qa']['evidence'].get('report')))
        require(isinstance(report, dict), 'QA report must be an object')
        require(report.get('source_sha256') == access['evidence']['source']['sha256'], 'QA report source hash differs')
        require(report.get('figure') == selection['evidence']['figure'] and
                report.get('pdf_page') == selection['evidence']['pdf_page'], 'QA report selected figure/page differs')
        require(report.get('artifact_sha256') == {kind: ref['sha256'] for kind, ref in artifacts.items()},
                'QA report must bind every current artifact SHA256')
        checks = report.get('checks')
        require(isinstance(checks, dict) and all(checks.get(key) == 'passed' for key in QA_CHECKS),
                'QA report must pass source_comparison, pptx_open_render and drawio_open_render')
        _text(report.get('notes'), 'QA notes')
        _text(report.get('reviewer'), 'QA reviewer')
    if stages['published']['status'] == 'passed':
        folder = _inside(root, stages['published']['evidence'].get('output_directory'), directory=True)
        require(folder.is_relative_to(root / 'output') and folder != root / 'output',
                'Published output must be a paper-scoped directory under output/')
        for kind, reference in artifacts.items():
            if kind != 'scene':
                require(_inside(root, reference['path']).is_relative_to(folder), 'Published artifact outside paper directory')
        require(_inside(root, access['evidence']['source']['path']).is_relative_to(folder),
                'Published paper directory must contain its verified original PDF')


def read_checkpoint(repository, paper_id, verify_files=False):
    root = Path(repository).resolve()
    record = read_json(_checkpoint_path(root, paper_id))
    _validate(root, record, verify_files=verify_files)
    require(record['paper_id'] == paper_id, 'Checkpoint id does not match filename')
    return record


def initialize_queue(repository, catalog='data/catalog.json'):
    """Import catalog claims once. Existing checkpoints are never reset or promoted."""
    root = Path(repository).resolve()
    catalog_path = _inside(root, str(catalog))
    document = read_json(catalog_path)
    require(isinstance(document, dict) and isinstance(document.get('papers'), list), 'Catalog papers list required')
    rows = document['papers']
    ids = []
    for row in rows:
        require(isinstance(row, dict), 'Catalog paper must be an object')
        ids.append(safe_id(row.get('id')))
        _text(row.get('title'), 'Catalog paper title')
        require(isinstance(row.get('status'), str) and row['status'] in {'not_reviewed', 'recreated', 'blocked', 'no_suitable_figure'}, 'Unsupported catalog import status')
        if row['status'] == 'blocked':
            _text(row.get('notes'), 'Blocked catalog evidence')
    require(len(set(ids)) == len(ids), 'Duplicate catalog paper id')
    digest = _sha(catalog_path)
    created = existing = 0
    for row in rows:
        with _lock(root, row['id']):
            path = _checkpoint_path(root, row['id'], True)
            if path.exists():
                read_checkpoint(root, row['id'])
                existing += 1
                continue
            evidence = {'summary': row.get('notes') or 'Imported catalog claim; independent checks still pending.',
                        'references': [str(catalog_path.relative_to(root)) + '#paper=' + row['id']],
                        'catalog_sha256': digest, 'imported_claim_only': True}
            stages = {name: {'status': 'pending', 'evidence': None} for name in STAGES}
            if row['status'] == 'recreated':
                stages['recreation'] = {'status': 'reported', 'evidence': copy.deepcopy(evidence)}
            if row['status'] == 'no_suitable_figure':
                stages['figure_selection'] = {'status': 'reported', 'evidence': copy.deepcopy(evidence)}
            imported_status = 'in_progress' if row['status'] == 'no_suitable_figure' else row['status']
            now = _now()
            record = {'schema_version': 1, 'paper_id': row['id'], 'revision': 1,
                      'status': imported_status, 'created_at': now, 'updated_at': now,
                      'catalog': {'path': str(catalog_path.relative_to(root)), 'sha256': digest,
                                  'source_commit': document.get('source_commit'), 'paper': copy.deepcopy(row)},
                      'stages': stages, 'terminal_evidence': evidence if row['status'] == 'blocked' else None,
                      'history': [{'revision': 1, 'at': now, 'actor': 'catalog-import', 'event': 'import',
                                   'catalog_sha256': digest, 'status': imported_status}]}
            _validate(root, record)
            _atomic_write(path, record)
            created += 1
    return {'created': created, 'existing': existing, 'catalog_papers': len(rows)}


def update_checkpoint(repository, paper_id, patch, expected_revision=None, actor='operator'):
    """Replace named stages with supplied evidence, validate, then atomically commit.

    expected_revision is optional for serialized writes; supply it to reject work
    based on an outdated checkpoint. Every successful call adds one audit event.
    """
    root = Path(repository).resolve()
    safe_id(paper_id)
    _text(actor, 'Actor')
    require(isinstance(patch, dict) and patch and set(patch) <= {'status', 'stages', 'terminal_evidence'},
            'Patch may only contain status, stages and terminal_evidence')
    _bytes(patch)
    with _lock(root, paper_id):
        old = read_checkpoint(root, paper_id)
        if expected_revision is not None:
            require(type(expected_revision) is int and expected_revision == old['revision'], 'Checkpoint revision conflict')
        result = copy.deepcopy(old)
        if 'stages' in patch:
            require(isinstance(patch['stages'], dict) and patch['stages'] and set(patch['stages']) <= set(STAGES),
                    'Patch has unknown or empty stages')
            result['stages'].update(copy.deepcopy(patch['stages']))
        if 'status' in patch:
            require(isinstance(patch['status'], str) and patch['status'] in STATUSES, 'Invalid checkpoint status')
            result['status'] = patch['status']
            if patch['status'] not in TERMINAL_STATUSES:
                result['terminal_evidence'] = None
            else:
                require('terminal_evidence' in patch, 'Terminal update requires explicit terminal_evidence')
        if 'terminal_evidence' in patch:
            result['terminal_evidence'] = copy.deepcopy(patch['terminal_evidence'])
        result['revision'] += 1
        result['updated_at'] = _now()
        result['history'].append({'revision': result['revision'], 'at': result['updated_at'], 'actor': actor,
                                  'event': 'update', 'previous_sha256': hashlib.sha256(_bytes(old)).hexdigest(),
                                  'patch': copy.deepcopy(patch)})
        _validate(root, result, verify_files=True)
        _atomic_write(_checkpoint_path(root, paper_id), result)
        return result


def queue_status(repository, verify_files=False):
    """Summarize valid checkpoints; fail loudly on damaged or unsafe records.

    verify_files rehashes passed-stage evidence. Without it, counts describe
    recorded state, not a fresh artifact or application validation.
    """
    root = Path(repository).resolve()
    counts = Counter({status: 0 for status in sorted(STATUSES)})
    stages = {name: Counter({status: 0 for status in sorted(STAGE_STATUSES)}) for name in STAGES}
    for path in sorted(_queue_dir(root).glob('*.json')):
        record = read_checkpoint(root, path.stem, verify_files=verify_files)
        counts[record['status']] += 1
        for name, stage in record['stages'].items():
            stages[name][stage['status']] += 1
    return {'total': sum(counts.values()), 'status': dict(counts),
            'stages': {name: dict(count) for name, count in stages.items()},
            'files_verified': verify_files}
