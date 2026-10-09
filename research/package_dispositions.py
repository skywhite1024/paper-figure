"""Stage source-only no-method-figure dispositions; publish only with --apply.

Never modifies surveys, catalog or queue. Returns suggested metadata/checkpoint
patches for the caller after publication. Requires PyMuPDF for PDF validation.
"""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from paper_figure.model import ValidationError, require
from paper_figure.queue import read_json, safe_id


def _json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def _text(value, label):
    require(isinstance(value, str) and value.strip(), f'{label} must be nonempty text')
    return value


def _title(value):
    return ''.join(char for char in unicodedata.normalize('NFKC', value).casefold() if char.isalnum())


def _prepare(root, survey_path):
    try:
        import fitz
    except ImportError as exc:
        raise ValidationError('PyMuPDF is required to validate source PDF page count and identity') from exc
    path = Path(survey_path)
    path = (path if path.is_absolute() else root / path).resolve()
    require(path.is_relative_to(root) and path.is_file(), 'Survey must be a repository file')
    survey = read_json(path)
    require(isinstance(survey, dict), 'Survey must be an object')
    paper_id = safe_id(survey.get('catalog_id'))
    require(survey.get('evidence_status') == 'no_method_figure', 'Explicit no_method_figure survey required')
    require(survey.get('figure_candidates') == [], 'No-method disposition cannot contain candidate figures')
    expected = _text(survey.get('title_expected') or survey.get('catalog_title'), 'Expected title')
    observed = _text(survey.get('pdf_title_observed'), 'Visually observed source title')
    catalog = read_json(root / 'data/catalog.json')
    require(isinstance(catalog, dict) and isinstance(catalog.get('papers'), list), 'Catalog papers required')
    matches = [paper for paper in catalog['papers'] if isinstance(paper, dict) and paper.get('id') == paper_id]
    require(len(matches) == 1 and _title(matches[0].get('title', '')) == _title(expected), 'Catalog identity differs')
    manual = survey.get('identity_reviewed') is True or survey.get('title_review_method') in ('manual_first_page', 'visual_first_page')
    require(survey.get('title_match') is True and (_title(expected) == _title(observed) or manual),
            'Reviewed source title must match the catalog')
    reason = _text(survey.get('review_notes'), 'Visual review reason')
    scope = _text(survey.get('no_method_figure_scope'), 'No-method scope')
    count = survey.get('page_count')
    require(type(count) is int and 0 < count <= 10000, 'Invalid surveyed page count')
    coverage = survey.get('visual_scan_coverage')
    require(isinstance(coverage, dict) and coverage.get('page_count') == count, 'Matching visual scan coverage required')
    pages = coverage.get('pages_scanned_1_based')
    require(isinstance(pages, list) and all(type(page) is int for page in pages)
            and sorted(set(pages)) == list(range(1, count + 1)), 'Every source page must have explicit visual scan coverage')
    require(coverage.get('contact_sheet_inspected') is True or coverage.get('all_pages_visually_inspected') is True,
            'Actual visual inspection must be explicitly recorded')
    version = survey.get('version')
    require(isinstance(version, str) and re.fullmatch(r'\d{4}\.\d{4,5}v[1-9]\d*', version),
            'A fixed arXiv version is required for this source-only packager')
    source_url = survey.get('versioned_pdf_url') or survey.get('pdf_url') or survey.get('source_url')
    _text(source_url, 'Fixed-version source URL')
    try:
        parsed = urlsplit(source_url)
        fixed = (parsed.scheme == 'https' and parsed.netloc in {'arxiv.org', 'www.arxiv.org'}
                 and parsed.path in {'/pdf/' + version, '/pdf/' + version + '.pdf'}
                 and not parsed.query and not parsed.fragment)
    except ValueError:
        fixed = False
    require(fixed, 'Source URL must identify the exact fixed arXiv PDF version')
    source_path = Path(_text(survey.get('pdf_path') or survey.get('pdf_local_path'), 'Source PDF path'))
    source_path = (source_path if source_path.is_absolute() else root / source_path).resolve()
    require(source_path.is_relative_to(root) or source_path.is_relative_to(Path('/tmp').resolve()),
            'Source PDF must stay within repository or /tmp')
    require(source_path.is_file() and source_path.suffix.lower() == '.pdf', 'Source PDF file missing')
    source_hash = survey.get('pdf_sha256')
    require(isinstance(source_hash, str) and re.fullmatch('[0-9a-f]{64}', source_hash), 'Invalid source SHA256')
    with source_path.open('rb') as stream:
        require(stream.read(5) == b'%PDF-', 'Source does not contain PDF bytes')
    require(_sha(source_path) == source_hash, 'Source PDF hash mismatch')
    try:
        with fitz.open(source_path) as document:
            require(not document.needs_pass and document.is_pdf, 'Readable unencrypted PDF required')
            require(document.page_count == count, 'Actual PDF page count differs from survey')
            first_page = document[0].get_text()
            require(_title(observed) in _title(first_page), 'Observed title not verified in actual first-page text')
            require(re.search(r'arXiv\s*:\s*' + re.escape(version) + r'(?![\w.])', first_page, re.I),
                    'Fixed version not verified in actual first-page text')
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f'Cannot parse source PDF: {exc}') from exc
    filename = 'paper-' + version + '.pdf'
    relative = Path('output') / paper_id
    review_snapshot = {key: value for key, value in survey.items()
                       if key not in {'pdf_path', 'pdf_local_path', 'visual_evidence_cache'}}
    disposition = {
        'schema_version': 1, 'catalog_id': paper_id, 'title': matches[0]['title'],
        'status': 'no_suitable_figure', 'delivery_kind': 'source_only_disposition',
        'editable_deliverable_count': 0, 'source_file': filename, 'source_url': source_url,
        'version': version, 'source_sha256': source_hash, 'page_count': count,
        'reviewed_pages': list(range(1, count + 1)), 'reason': reason, 'scope': scope,
        'references': [source_url, str(path.relative_to(root))],
        'survey': {'repository_path': str(path.relative_to(root)), 'sha256': _sha(path),
                   'review_sha256': hashlib.sha256(_json(review_snapshot)).hexdigest()},
        'identity_evidence': {'observed_title': observed, 'title_match': True,
                              'review_basis': 'explicit_first_page_review' if manual else 'full_visual_scan_including_first_page',
                              'first_page_title_text_verified': True, 'first_page_version_verified': True},
        'visual_scan_coverage': copy.deepcopy(coverage), 'license_note': survey.get('license_note'),
        'inspected_at': survey.get('inspected_at'),
    }
    readme = ('# ' + matches[0]['title'] + '\n\n'
        'Status: no suitable architecture/process figure found in the reviewed source.\n\n'
        'This is a source-only disposition, not an editable figure delivery. It does not claim that the paper has no illustrations. '
        'The paper may contain photographs, result charts, trajectories, mathematical illustrations or pseudocode. '
        'No architecture or process diagram has been invented from those materials.\n\n'
        f'- [Exact-version source PDF]({filename})\n- [Disposition and review evidence](disposition.json)\n'
        f'- Official fixed version: {source_url}\n- Source SHA256: {source_hash}\n'
        f'- All {count} PDF pages are recorded as visually reviewed\n- Editable deliverables: 0\n\n'
        f'## Review finding\n\n{reason}\n\n## Scope\n\n{scope}\n\n'
        'The source PDF is preserved byte-for-byte for private reference. This bundle does not grant redistribution rights; '
        'retain the original copyright and license terms.\n').encode('utf-8')
    return source_path, relative, disposition, readme


@contextmanager
def _lock(root, paper_id):
    import fcntl
    folder = root / 'build/disposition-locks'
    require(folder.resolve().is_relative_to(root), 'Disposition lock directory escapes repository')
    folder.mkdir(parents=True, exist_ok=True)
    fd = os.open(folder / (paper_id + '.lock'), os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _equivalent(existing, expected):
    # Moving the cache PDF into this bundle changes only the survey's locator and
    # raw hash. Keep the original auditable survey hash if review evidence agrees.
    existing, expected = copy.deepcopy(existing), copy.deepcopy(expected)
    for value in (existing, expected):
        if isinstance(value.get('survey'), dict):
            value['survey'].pop('sha256', None)
    return existing == expected


def _existing(folder, disposition, readme):
    require(folder.is_dir() and not folder.is_symlink(), 'Existing output must be a regular directory')
    expected = {disposition['source_file'], 'README.md', 'disposition.json'}
    require({path.name for path in folder.iterdir()} == expected, 'Refusing to overwrite an existing editable or different output folder')
    require(not any(path.is_symlink() for path in folder.iterdir()), 'Disposition files cannot be symlinks')
    old = read_json(folder / 'disposition.json')
    require(isinstance(old, dict) and _equivalent(old, disposition), 'Existing disposition evidence differs; refusing overwrite')
    require(_sha(folder / disposition['source_file']) == disposition['source_sha256'], 'Existing source PDF hash mismatch')
    require((folder / 'README.md').read_bytes() == readme, 'Existing disposition README differs; refusing overwrite')
    return old


def package_disposition(repository, survey_path, apply=False):
    """Validate and optionally atomically publish one immutable source-only bundle.

    Only output/<catalog-id>/ and a build/ lock are written. Returned survey_patch
    and queue_patch are instructions for the caller; this function never applies them.
    """
    root = Path(repository).resolve()
    source, relative, disposition, readme = _prepare(root, survey_path)
    folder = root / relative
    require(folder.resolve().is_relative_to(root) and not folder.is_symlink(), 'Output path escapes repository or is a symlink')
    action = 'planned'
    if apply:
        with _lock(root, disposition['catalog_id']):
            if folder.exists():
                disposition = _existing(folder, disposition, readme)
                action = 'unchanged'
            else:
                folder.parent.mkdir(parents=True, exist_ok=True)
                stage = Path(tempfile.mkdtemp(prefix='.disposition-' + disposition['catalog_id'] + '-', dir=folder.parent))
                try:
                    shutil.copyfile(source, stage / disposition['source_file'])
                    require(_sha(stage / disposition['source_file']) == disposition['source_sha256'], 'Staged source hash mismatch')
                    (stage / 'README.md').write_bytes(readme)
                    (stage / 'disposition.json').write_bytes(_json(disposition))
                    for path in stage.iterdir():
                        with path.open('rb') as stream:
                            os.fsync(stream.fileno())
                    stage_fd = os.open(stage, os.O_RDONLY)
                    try:
                        os.fsync(stage_fd)
                    finally:
                        os.close(stage_fd)
                    require(not folder.exists(), 'Output appeared during staging; refusing overwrite')
                    os.rename(stage, folder)
                    parent_fd = os.open(folder.parent, os.O_RDONLY)
                    try:
                        os.fsync(parent_fd)
                    finally:
                        os.close(parent_fd)
                    action = 'created'
                finally:
                    if stage.exists():
                        shutil.rmtree(stage)
    elif folder.exists():
        disposition = _existing(folder, disposition, readme)
        action = 'unchanged'
    source_ref = {'path': str(relative / disposition['source_file']), 'sha256': disposition['source_sha256']}
    references = [str(relative / 'disposition.json')] + disposition['references']
    evidence = {'summary': disposition['reason'], 'references': references,
                'disposition_path': str(relative / 'disposition.json')}
    queue_patch = {'status': 'no_suitable_figure', 'terminal_evidence': copy.deepcopy(evidence), 'stages': {
        'source_identity': {'status': 'passed', 'evidence': {**evidence, 'matches_catalog': True,
            'observed_title': disposition['identity_evidence']['observed_title'], 'source_url': disposition['source_url'],
            'source_sha256': disposition['source_sha256'], 'review_basis': disposition['identity_evidence']['review_basis']}},
        'source_access': {'status': 'passed', 'evidence': {**evidence, 'source': source_ref, 'page_count': disposition['page_count']}},
        'figure_selection': {'status': 'failed', 'evidence': {**evidence, 'reviewed_pages': disposition['reviewed_pages'],
            'scope': disposition['scope'], 'visual_scan_coverage': disposition['visual_scan_coverage']}}}}
    return {'action': action, 'applied': apply, 'paper_id': disposition['catalog_id'], 'output_directory': str(relative),
            'source': source_ref, 'disposition': disposition, 'survey_patch': {'pdf_path': source_ref['path']},
            'queue_patch': queue_patch, 'editable_deliverable_count': 0,
            'next_step': 'Only after bundle creation: review and separately apply survey_patch and queue_patch using the current queue revision.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--apply', action='store_true', help='Publish new validated bundles; default only plans')
    parser.add_argument('surveys', nargs='+', type=Path)
    args = parser.parse_args(argv)
    results = []
    for path in args.surveys:
        try:
            results.append(package_disposition(args.repository, path, args.apply))
        except (OSError, ValidationError) as exc:
            results.append({'action': 'error', 'survey': str(path), 'error': str(exc)})
    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    return 2 if any(result['action'] == 'error' for result in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
