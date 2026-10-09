"""Import source survey evidence into queue checkpoints, without copying PDFs.

Temporary/build PDFs remain reported access. Candidate lists are not selections.
Machine-only title comparisons cannot approve identity or terminal mismatches.
Existing reviewed terminal decisions and active downstream work are preserved;
legacy importer-only approvals lacking review evidence are corrected on reimport.
"""
import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from paper_figure.model import ValidationError, require
from paper_figure.queue import TERMINAL_STATUSES, read_checkpoint, read_json, safe_id, update_checkpoint


def _sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _title(value):
    return ''.join(char for char in unicodedata.normalize('NFKC', value).casefold() if char.isalnum())


def _url(survey):
    for key in ('versioned_pdf_url', 'pdf_url', 'source_url', 'paper_url'):
        value = survey.get(key)
        if _text(value):
            try:
                parsed = urlsplit(value)
                if parsed.scheme in {'http', 'https'} and parsed.netloc:
                    return value
            except ValueError:
                pass
    return None


def _source(root, survey):
    """Verify explicitly referenced local PDF bytes, without treating cache as durable."""
    value = survey.get('pdf_path') or survey.get('pdf_local_path')
    sha = survey.get('pdf_sha256')
    result = {'reported_path': value, 'reported_sha256': sha, 'verified_locally': False,
              'durable': False, 'reason': 'No locally verifiable source PDF was supplied.'}
    if not _text(value):
        return result
    path = Path(value)
    path = (path if path.is_absolute() else root / path).resolve()
    require(path.is_relative_to(root) or path.is_relative_to(Path('/tmp').resolve()),
            'Survey PDF must be inside the repository or /tmp')
    require(path.suffix.lower() == '.pdf', 'Survey source must reference a PDF filename')
    if not path.is_file():
        result['reason'] = 'Reported PDF is no longer present; only survey metadata is retained.'
        return result
    require(isinstance(sha, str) and re.fullmatch('[0-9a-f]{64}', sha), 'Survey source requires a valid SHA256')
    with path.open('rb') as stream:
        require(stream.read(5) == b'%PDF-', 'Survey source is not PDF bytes')
    require(_sha(path) == sha, 'Survey PDF hash mismatch')
    result['verified_locally'] = True
    output = root / 'output'
    result['durable'] = path.is_relative_to(output) and len(path.relative_to(output).parts) >= 2
    if result['durable']:
        result['source'] = {'path': str(path.relative_to(root)), 'sha256': sha}
        result['reason'] = 'PDF bytes and SHA256 verified in a durable paper-scoped output directory.'
    else:
        result['reason'] = 'PDF bytes and SHA256 verified in temporary/build storage; durable output copy is still needed.'
    return result


def _coverage(survey):
    coverage = survey.get('visual_scan_coverage')
    count = survey.get('page_count')
    if not isinstance(coverage, dict) or type(count) is not int or count <= 0:
        return None
    pages = coverage.get('pages_scanned_1_based')
    if not (isinstance(pages, list) and all(type(page) is int for page in pages)
            and set(pages) == set(range(1, count + 1))):
        return None
    if coverage.get('page_count') != count or not (coverage.get('contact_sheet_inspected') is True
                                                 or coverage.get('all_pages_visually_inspected') is True):
        return None
    if not _text(survey.get('review_notes')) or not _text(survey.get('no_method_figure_scope')):
        return None
    return sorted(set(pages))


def survey_patch(repository, survey_path):
    """Build a conservative queue patch; never write source, catalog, or queue files."""
    root = Path(repository).resolve()
    path = Path(survey_path)
    path = (path if path.is_absolute() else root / path).resolve()
    require(path.is_relative_to(root) and path.is_file(), 'Survey evidence must be a repository file')
    survey = read_json(path)
    require(isinstance(survey, dict), 'Survey must be a JSON object')
    if 'catalog_id' not in survey:
        return {'action': 'skipped', 'reason': 'not_a_source_survey', 'survey': str(path.relative_to(root))}
    paper_id = safe_id(survey['catalog_id'])
    current = read_checkpoint(root, paper_id)
    expected = survey.get('title_expected') or survey.get('catalog_title')
    require(_text(expected) and _title(expected) == _title(current['catalog']['paper']['title']),
            'Survey expected title does not match its catalog checkpoint')
    context = {'paper_id': paper_id, 'survey': str(path.relative_to(root)), 'revision': current['revision']}
    legacy_machine_mismatch = (current['status'] == 'source_mismatch'
        and current.get('terminal_evidence', {}).get('survey_import') is True
        and not current['stages']['source_identity']['evidence'].get('identity_review_basis'))
    if current['status'] in TERMINAL_STATUSES and not legacy_machine_mismatch:
        return {**context, 'action': 'skipped', 'reason': 'preserved_terminal_decision'}
    if any(current['stages'][name]['status'] in {'in_progress', 'passed'} for name in ('recreation', 'qa', 'published')):
        return {**context, 'action': 'skipped', 'reason': 'preserved_active_downstream_work'}
    source = _source(root, survey)
    url = _url(survey)
    reference = str(path.relative_to(root))
    common = {'references': [reference] + ([url] if url else []), 'survey_import': True,
              'survey': {'path': reference, 'sha256': _sha(path)},
              'version': survey.get('version'), 'license_note': survey.get('license_note'),
              'review_notes': survey.get('review_notes'), 'inspected_at': survey.get('inspected_at')}

    def stage(status, summary, **extra):
        return {'status': status, 'evidence': {**copy.deepcopy(common), 'summary': summary, **extra}}

    proposed = {}
    count = survey.get('page_count')
    count_valid = type(count) is int and count > 0
    candidates = survey.get('figure_candidates', [])
    require(isinstance(candidates, list) and all(isinstance(candidate, dict) for candidate in candidates),
            'figure_candidates must be a list of objects')
    coverage = _coverage(survey)
    explicit_identity_review = (survey.get('identity_reviewed') is True or
                                survey.get('title_review_method') in ('manual_first_page', 'visual_first_page'))
    review_basis = ('explicit_first_page_identity_review' if explicit_identity_review else
                    'visually_inspected_source_candidate' if any(c.get('visually_inspected') is True for c in candidates) else
                    'full_source_visual_scan' if coverage else None)
    mismatch_reason = survey.get('identity_mismatch_reason') or survey.get('mismatch_reason')
    observed = survey.get('pdf_title_observed') or survey.get('first_page_title_text')
    identity_pass = (source['verified_locally'] and survey.get('title_match') is True and review_basis and
                     _text(observed) and (_title(observed) == _title(expected) or explicit_identity_review) and bool(url))
    identity_failed = (source['verified_locally'] and survey.get('title_match') is False and
                       explicit_identity_review and _text(mismatch_reason) and
                       _text(observed) and _title(observed) != _title(expected) and bool(url))
    identity_extra = {'expected_title': expected, 'observed_title': observed, 'source_url': url,
                      'source_sha256': survey.get('pdf_sha256'), 'reported_title_match': survey.get('title_match'),
                      'identity_review_basis': review_basis, 'identity_reviewed': survey.get('identity_reviewed'),
                      'title_review_method': survey.get('title_review_method'), 'mismatch_reason': mismatch_reason}
    if identity_pass:
        proposed['source_identity'] = stage('passed', 'Survey title matched the catalog; referenced PDF bytes and hash were verified.',
                                            matches_catalog=True, **identity_extra)
    elif identity_failed:
        proposed['source_identity'] = stage('failed', mismatch_reason,
                                            matches_catalog=False, **identity_extra)
    else:
        proposed['source_identity'] = stage('reported', 'Survey identity claim retained; source/title evidence is not sufficient to pass identity.',
                                            **identity_extra)
    if source['durable'] and count_valid:
        proposed['source_access'] = stage('passed', source['reason'], source=source['source'], page_count=count)
    else:
        proposed['source_access'] = stage('reported', source['reason'], observed_source=source, page_count=count,
                                          source_status=survey.get('source_status'))

    source_status = survey.get('source_status')
    inaccessible = (source_status == 'inaccessible' and _text(survey.get('review_notes')) and bool(url)
                    and not source['verified_locally'])
    if inaccessible:
        proposed['source_access'] = stage('failed', survey['review_notes'], source_status=source_status,
                                          access_attempts=survey.get('access_attempts'), http_status=survey.get('http_status'))
    no_method = survey.get('evidence_status') == 'no_method_figure' or source_status == 'no_method_figure'
    no_figure = bool(no_method and not candidates and coverage and identity_pass and source['durable'] and count_valid)
    if no_figure:
        proposed['figure_selection'] = stage('failed', survey['review_notes'], reviewed_pages=coverage,
                                              scope=survey['no_method_figure_scope'], visual_scan_coverage=survey['visual_scan_coverage'])
    elif candidates or no_method:
        proposed['figure_selection'] = stage('reported',
            'Survey candidates/review retained; candidate lists and incomplete source evidence do not certify a selected deliverable.',
            figure_candidates=candidates, reviewed_pages=coverage, no_method_figure_reported=no_method,
            visual_scan_coverage=survey.get('visual_scan_coverage'), scope=survey.get('no_method_figure_scope'))

    # Passing stages and externally managed work retain their original evidence.
    changes = {}
    for name, candidate in proposed.items():
        previous = current['stages'][name]
        if previous['status'] == 'passed':
            old_hash = (previous['evidence'].get('source_sha256') if name == 'source_identity'
                        else previous['evidence'].get('source', {}).get('sha256') if name == 'source_access' else None)
            if old_hash and survey.get('pdf_sha256') and old_hash != survey['pdf_sha256']:
                return {**context, 'action': 'skipped', 'reason': 'source_conflicts_with_verified_checkpoint'}
            # Correct only legacy importer approvals lacking a recorded review basis.
            if (name == 'source_identity' and previous['evidence'].get('survey_import') is True
                    and not previous['evidence'].get('identity_review_basis') and candidate != previous):
                changes[name] = candidate
            continue
        if previous['status'] != 'pending' and not previous['evidence'].get('survey_import'):
            continue
        if candidate != previous:
            changes[name] = candidate
    effective = {**current['stages'], **changes}
    patch = {'stages': changes} if changes else {}
    outcome = None
    if identity_failed and effective['source_identity']['status'] == 'failed':
        outcome = 'source_mismatch'
    elif inaccessible and effective['source_access']['status'] == 'failed':
        outcome = 'inaccessible'
    elif no_figure and effective['figure_selection']['status'] == 'failed' and all(
            effective[name]['status'] == 'passed' for name in ('source_identity', 'source_access')):
        outcome = 'no_suitable_figure'
    if outcome:
        patch['status'] = outcome
        patch['terminal_evidence'] = {**copy.deepcopy(common), 'summary':
            (mismatch_reason if outcome == 'source_mismatch' else survey.get('review_notes')
             or f'Explicit surveyed source outcome: {outcome}'),
            'outcome': outcome, 'observed_source': source}
    elif changes and (current['status'] == 'not_reviewed' or legacy_machine_mismatch):
        patch['status'] = 'in_progress'
    return {**context, 'action': 'update' if patch else 'unchanged', 'patch': patch}


def import_survey(repository, survey_path, dry_run=False):
    result = survey_patch(repository, survey_path)
    if result['action'] == 'update':
        if dry_run:
            result['action'] = 'would_update'
        else:
            updated = update_checkpoint(repository, result['paper_id'], result['patch'],
                                         expected_revision=result['revision'], actor='survey-import')
            result['action'] = 'updated'
            result['revision'] = updated['revision']
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--survey-dir', type=Path, default=Path('research/survey'))
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('files', nargs='*', type=Path)
    args = parser.parse_args(argv)
    args.repository = args.repository.resolve()
    folder = args.survey_dir if args.survey_dir.is_absolute() else args.repository / args.survey_dir
    if not args.files and not folder.is_dir():
        parser.error(f'Survey directory does not exist: {folder}')
    files = args.files or sorted(folder.glob('*.json'))
    results = []
    for path in files:
        try:
            results.append(import_survey(args.repository, path, args.dry_run))
        except (OSError, ValidationError) as exc:
            results.append({'action': 'error', 'survey': str(path), 'error': str(exc)})
    counts = {action: sum(row['action'] == action for row in results) for action in
              ('updated', 'would_update', 'unchanged', 'skipped', 'error')}
    print(json.dumps({'counts': counts, 'results': results}, ensure_ascii=False, indent=2))
    return 2 if counts['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
