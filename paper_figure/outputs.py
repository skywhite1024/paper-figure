"""Validate and index paper-scoped deliverables without rewriting artifact bytes."""
import os
import hashlib
import base64
import xml.etree.ElementTree as ET
import html
import json
import re
import shutil
import tempfile
from pathlib import Path

from .model import ValidationError, require, local_asset


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_file(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f'{path}: {exc}') from exc


def local_file(folder, filename):
    require(isinstance(filename, str) and Path(filename).name == filename,
            'Artifact filenames must be local basenames')
    path = folder / filename
    require(path.is_file() and path.resolve().is_relative_to(folder.resolve()),
            f'Missing or unsafe artifact: {path}')
    return path


def read_paper(folder, repository):
    """Cross-check source identity, export manifest and exact original PDF bytes."""
    sources = json_file(folder / 'sources.json')
    require(isinstance(sources.get('papers'), list) and len(sources['papers']) == 1,
            f'{folder}: exactly one paper expected')
    paper = sources['papers'][0]
    require(paper.get('id') == folder.name and re.fullmatch(r'[a-z0-9_-]+', folder.name),
            'Paper id must match directory name')
    pdf = local_file(folder, paper['file'])
    require(sha256(pdf) == paper['sha256'], f'{pdf}: source PDF hash mismatch')
    scene_path = (folder / paper['diagram_json']).resolve()
    require(scene_path.is_relative_to(repository.resolve() / 'data'),
            'Scene reference must stay in repository data/')
    scene = json_file(scene_path)
    require(scene['provenance']['figure'] == paper['figure'] and
            scene['provenance']['page'] == paper['pdf_page_1_based'], 'Source figure/page mapping differs')
    if paper.get('arxiv_id_version'):
        require(paper['arxiv_id_version'] in scene['provenance']['paper_url'], 'Source paper version differs')
    if 'source_sha256' in scene['provenance']:
        require(scene['provenance']['source_sha256'] == paper['sha256'], 'Scene and original PDF hashes differ')
    stem = scene['id']
    require(re.fullmatch(r'[A-Za-z0-9_-]+', stem), 'Invalid diagram id')
    manifest = json_file(folder / (stem + '.manifest.json'))
    require(manifest['diagram_id'] == stem and manifest['source_sha256'] == sha256(scene_path),
            f'{folder}: scene and export manifest differ')
    entries = {entry['name']: entry for entry in manifest['files']}
    for suffix in ['pptx', 'drawio', 'png']:
        name = stem + '.' + suffix
        path = local_file(folder, name)
        require(name in entries and sha256(path) == entries[name]['sha256'],
                f'{path}: export hash mismatch')
    image_nodes = [n for n in scene['nodes'] if n['shape'] == 'image']
    assets = {n['asset']: sha256(local_asset(scene_path.parent, n['asset'])) for n in image_nodes}
    if 'assets' in manifest:
        require({entry['name']: entry['sha256'] for entry in manifest['assets']} == assets, 'Raster source assets differ from export manifest')
    if image_nodes:
        try:
            cells = {c.get('id'): c for c in ET.parse(folder/(stem+'.drawio')).iter('mxCell')}
            for node in image_nodes:
                style = cells[node['id']].get('style', '')
                match = re.search(r'(?:^|;)image=data:image/(?:png|jpeg),([^;]+)(?:;|$)', style)
                require(match is not None, 'Missing embedded draw.io raster source')
                embedded = base64.b64decode(match.group(1), validate=True)
                require(hashlib.sha256(embedded).hexdigest() == assets[node['asset']], 'Source asset differs from actual embedded draw.io bytes')
        except (ET.ParseError, ValueError, KeyError) as exc:
            raise ValidationError('Invalid or stale embedded raster asset: '+str(exc)) from exc
    qa_path = folder / 'VALIDATION.json'
    if qa_path.is_file():
        qa = json_file(qa_path)
        if 'source_scene_sha256' in qa:
            require(qa['source_scene_sha256'] == manifest['source_sha256'], 'QA report binds an older scene')
        if 'source_pdf_sha256' in qa:
            require(qa['source_pdf_sha256'] == paper['sha256'], 'QA report binds another source PDF')
        for entry in qa.get('checked_files', []):
            require(sha256(local_file(folder, entry['name'])) == entry['sha256'], 'QA report binds older exported bytes')
    original = local_file(folder, folder.name + '-original.png')
    require(paper['editable_pptx'] == stem + '.pptx' and
            paper['editable_drawio'] == stem + '.drawio', 'Stale editable-file reference')
    return paper, scene, manifest, original


STYLE = '''body{font:16px system-ui;background:#f4f6f8;color:#16212b;margin:24px}
main{max-width:1600px;margin:auto}section{background:white;padding:18px;border-radius:10px}
img{max-width:100%;height:auto;border:1px solid #ddd}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
a{color:#17629e}small{color:#56636e}@media(max-width:900px){.pair{grid-template-columns:1fr}}'''


def refresh_output(repository, output=None):
    """Generate per-paper docs/hash inventories and small shared indexes.

    Existing PPTX/drawio/PNG/PDF bytes are never modified. Checks happen before
    any metadata is written, so a stale or corrupt artifact fails explicitly.
    """
    repository = Path(repository).resolve()
    output = Path(output or repository / 'output').resolve()
    require(output.is_dir(), 'Output directory does not exist')
    folders = sorted(p.parent for p in output.glob('*/sources.json'))
    require(folders, 'No paper directories containing sources.json')
    records = [(folder, *read_paper(folder, repository)) for folder in folders]
    dispositions = []
    for path in sorted(output.glob('*/disposition.json')):
        disposition = json_file(path)
        require(disposition.get('status') == 'no_suitable_figure' and disposition.get('editable_deliverable_count') == 0, 'Invalid source-only disposition')
        source_pdf = local_file(path.parent, disposition['source_file'])
        require(sha256(source_pdf) == disposition['source_sha256'], 'Disposition source PDF hash mismatch')
        require(disposition.get('catalog_id') == path.parent.name and re.fullmatch(r'[a-z0-9_-]+', path.parent.name), 'Disposition directory identity mismatch')
        require(set(disposition['reviewed_pages']) == set(range(1, disposition['page_count']+1)), 'Disposition lacks full source coverage')
        local_file(path.parent, 'README.md')
        dispositions.append((path.parent.name, disposition['title']))
    links = []
    for folder, paper, scene, manifest, original in records:
        stem = scene['id']
        title = paper['title']
        figure = paper['figure']
        page = paper['pdf_page_1_based']
        typeable_text = sum(bool(n.get('label', '').strip()) and n['shape'] != 'image' for n in scene['nodes']) + sum(bool(e.get('label', '').strip()) for e in scene['edges'])
        native_paths = sum(n['shape'] == 'path' for n in scene['nodes'])
        raster_count = sum(n['shape'] == 'image' for n in scene['nodes'])
        source_version = paper.get('arxiv_id_version') or paper.get('source_version') or paper.get('publication_version') or 'source version recorded in sources.json'
        text = [f'# {title}', '', f'{figure} · PDF 第 {page} 页 · {source_version}', '',
                f'- [PowerPoint]({stem}.pptx)', f'- [draw.io]({stem}.drawio)',
                f'- [重建预览]({stem}.png)', f'- [论文原图]({original.name})',
                '- [原图与重建离线对照](comparison.html)', f'- [原文 PDF]({paper["file"]})',
                '- [来源与版本记录](sources.json)', f'- [导出清单与原生对象统计]({stem}.manifest.json)',
                '- [本文件夹 SHA256 清单](bundle.manifest.json)', '- [验证记录](VALIDATION.json)', '',
                '## 来源与编辑边界', '', f'可直接键入修改的文字对象：{typeable_text}；原生自由路径：{native_paths}；独立栅格对象：{raster_count}（内部像素不可编辑，可能包含照片、图标或源图公式，详见下方说明）。字形轮廓可移动/改色/编辑点，但不能像文本框一样直接改字；数学轮廓不是可输入新公式的公式对象。', '', f'官方固定版本：{paper["source_url"]}', '',
                scene['provenance']['notes'], '', scene['provenance']['license'], '',
                '自由路径可编辑，但不会自动吸附到语义节点。独立栅格照片/图标的内部像素不是可编辑对象。',
                '这是用户要求的私有仓库对照副本，不代表取得公开再发布许可。', '',
                f'原文 SHA256：`{paper["sha256"]}`', '', '[返回论文索引](../README.md)', '']
        (folder / 'README.md').write_text('\n'.join(text), encoding='utf-8')
        page_html = f'''<!doctype html><html lang="zh"><meta charset="utf-8">
<title>{html.escape(title)} · 原图对照</title><style>{STYLE}</style><main>
<p><a href="../comparison.html">返回论文索引</a> · <a href="README.md">来源与编辑说明</a></p>
<h1>{html.escape(title)}</h1><p>{html.escape(figure)}，PDF 第 {page} 页</p>
<p><a href="{stem}.pptx">PowerPoint</a> · <a href="{stem}.drawio">draw.io</a> ·
<a href="{html.escape(paper['file'], quote=True)}">原文 PDF ({html.escape(source_version)})</a></p>
<section class="pair"><div><h2>论文原图</h2><img src="{original.name}" alt="论文原图"></div>
<div><h2>可编辑重建预览</h2><img src="{stem}.png" alt="重建预览"></div></section>
<p>{html.escape(scene['provenance']['notes'])}</p>
<p>请编辑 PPTX / draw.io；预览 PNG 和照片内部像素不因此成为可编辑对象。</p></main></html>'''
        (folder / 'comparison.html').write_text(page_html, encoding='utf-8')
        tracked = [stem + suffix for suffix in ['.pptx', '.drawio', '.png', '.manifest.json']]
        tracked += [original.name, paper['file'], 'sources.json', 'README.md', 'comparison.html', 'VALIDATION.json']
        inventory = {'paper_id': paper['id'], 'diagram_id': stem,
                     'source_sha256': manifest['source_sha256'],
                     'files': [{'name': name, 'bytes': local_file(folder, name).stat().st_size,
                                'sha256': sha256(folder / name)} for name in sorted(tracked)]}
        (folder / 'bundle.manifest.json').write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n')
        links.append((folder.name, title, figure, page))
    index = ['# 论文结果索引', '', '每篇论文单独一个文件夹，包含 PPTX、draw.io、预览、论文原图、原文 PDF、离线对照及来源/校验记录。', '']
    index.extend(f'- [{title}]({slug}/README.md)：{figure}，PDF 第 {page} 页 · [离线对照]({slug}/comparison.html)'
                 for slug, title, figure, page in links)
    if dispositions:
        index += ['', '## 已核查原文但未发现适合转换的方法结构图', '', '这些仅归档原文与逐页核查说明，不计入可编辑图交付数。']
        index.extend(f'- [{title}]({slug}/README.md)' for slug, title in dispositions)
    if (output / 'PROCESSING.json').exists():
        index += ['', '[逐篇处理进度（已交付与待审查分开计数）](PROCESSING.json)']
    index += ['', '[验证汇总](VALIDATION.json) · [本地 HTML 索引](comparison.html)', '',
              '仓库不上传 ZIP；源代码位于仓库根目录，旧语义简化版在 data/diagrams/legacy/。',
              '保留来源版权与许可证说明；私有仓库上传不代表公开再发布许可。', '']
    (output / 'README.md').write_text('\n'.join(index), encoding='utf-8')
    (output / 'comparison.html').write_text(
        f'<!doctype html><html lang="zh"><meta charset="utf-8"><title>论文结果索引</title><style>{STYLE}</style><main><h1>论文结果索引</h1><ul>' +
        ''.join(f'<li><a href="{slug}/comparison.html">{html.escape(title)}</a> · {html.escape(figure)}，PDF 第 {page} 页 · <a href="{slug}/README.md">文件与来源</a></li>'
                for slug, title, figure, page in links) + '</ul>' + ('<h2>未发现适合的方法结构图（仅原文与核查记录）</h2><ul>' + ''.join(f'<li><a href="{slug}/README.md">{html.escape(title)}</a></li>' for slug,title in dispositions) + '</ul>' if dispositions else '') + '<p>每篇论文的原文 PDF 与可编辑结果保存在同一文件夹。</p></main></html>', encoding='utf-8')
    return {'papers': [slug for slug, *_ in links], 'artifacts_modified': False}


def publish_build(repository, build, output=None, papers=None):
    """Copy checked regenerated diagram files into the existing paper folders.

    Original PDFs and source comparison PNGs already in those folders are kept.
    No downloads, artifact duplication, or flat output layout is introduced.
    """
    repository, build = Path(repository).resolve(), Path(build).resolve()
    output = Path(output or repository / 'output').resolve()
    plans = []
    changed = []
    selected = set(papers) if papers is not None else None
    require(selected is None or selected and all(isinstance(x, str) and re.fullmatch(r'[a-z0-9_-]+', x) for x in selected), 'Invalid paper selection')
    found = set()
    for folder in sorted(p.parent for p in output.glob('*/sources.json')):
        if selected is not None and folder.name not in selected:
            continue
        found.add(folder.name)
        paper = json_file(folder / 'sources.json')['papers'][0]
        scene = json_file((folder / paper['diagram_json']).resolve())
        stem = scene['id']
        generated = build / folder.name
        manifest_path = generated / (stem + '.manifest.json')
        manifest = json_file(manifest_path)
        require(manifest['source_sha256'] == sha256((folder / paper['diagram_json']).resolve()),
                'Generated scene hash is stale')
        entries = {e['name']: e for e in manifest['files']}
        for suffix in ['pptx', 'drawio', 'png']:
            name = stem + '.' + suffix
            source = local_file(generated, name)
            require(name in entries and sha256(source) == entries[name]['sha256'], 'Generated file hash mismatch')
            plans.append((source, folder / name))
        old_manifest = json_file(folder / manifest_path.name)
        if old_manifest != manifest:
            changed.append((folder, stem, manifest, old_manifest))
        plans.append((manifest_path, folder / manifest_path.name))
    require(selected is None or selected == found, 'Unknown selected paper')
    require(plans, 'No paper builds to publish')
    # Validate the complete proposed folder tree before touching published files.
    # Sibling staging keeps ../../data scene references equivalent to output/.
    modified = any(not target.is_file() or sha256(source) != sha256(target)
                   for source, target in plans)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.output-stage-') as temporary:
        stage = Path(temporary)
        shutil.copytree(output, stage, dirs_exist_ok=True)
        for source, target in plans:
            staged_target = stage / target.relative_to(output)
            shutil.copy2(source, staged_target)
        for folder, stem, manifest, previous in changed:
            validation = {'review_status': 'pending after regeneration',
                          'note': 'Prior visual and application checks do not certify these newly generated bytes.',
                          'figures': {stem: {'source_sha256': manifest['source_sha256'], 'metrics': manifest['metrics']}},
                          'previous_source_sha256': previous['source_sha256']}
            staged_folder = stage / folder.relative_to(output)
            (staged_folder / 'VALIDATION.json').write_text(json.dumps(validation, indent=2, ensure_ascii=False) + '\n')
        result = refresh_output(repository, stage)
        for source in stage.rglob('*'):
            if source.is_file():
                target = output / source.relative_to(stage)
                if not target.exists() or sha256(source) != sha256(target):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    result['artifacts_modified'] = modified
    return result


def add_papers(repository, candidates, output=None):
    """Validate and register a batch with one staging copy of the existing tree.

    Existing paper replacement is refused; use publish_build for regeneration.
    All candidate hashes and the complete proposed tree are checked before any
    new folder is moved into output. Source references retain ../../data/.
    """
    repository = Path(repository).resolve()
    candidates = [Path(candidate).resolve() for candidate in candidates]
    output = Path(output or repository / 'output').resolve()
    require(candidates and len({c.name for c in candidates}) == len(candidates), 'Empty or duplicate paper batch')
    for candidate in candidates:
        require(bool(re.fullmatch(r'[a-z0-9_-]+', candidate.name)), 'Unsafe paper slug')
        require(not (output / candidate.name).exists(), 'Paper output already exists')
        require(candidate.is_dir() and not any(p.is_symlink() for p in candidate.rglob('*')), 'Unsafe candidate directory')
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.output-stage-') as temporary:
        stage = Path(temporary)
        shutil.copytree(output, stage, dirs_exist_ok=True)
        for candidate in candidates:
            shutil.copytree(candidate, stage / candidate.name)
        refresh_output(repository, stage)
        # Each validated directory moves atomically on the same filesystem.
        for candidate in candidates:
            os.replace(stage / candidate.name, output / candidate.name)
        for name in ['README.md', 'comparison.html']:
            os.replace(stage / name, output / name)
    return [{'paper': c.name, 'path': str(output / c.name)} for c in candidates]


def add_paper(repository, candidate, output=None):
    """Backwards-compatible single-bundle registration."""
    return add_papers(repository, [candidate], output)[0]
