#!/usr/bin/env python3
"""Independently compare scene objects with the exported PPTX's OOXML.

Examples (from any working directory):
    python research/verify_pptx_geometry.py
    python research/verify_pptx_geometry.py output/aspire output/roboreact
    python research/verify_pptx_geometry.py build/candidates/gordon --output-dir build/qa

By default, inspect repository output folders containing sources.json. Relative
folder/output arguments are repository-relative. Reports are written below
build/ooxml_geometry_qa unless --output-dir is supplied. No office application
or shared user profile is opened. This does not establish application rendering,
font/layout fidelity, semantic connector routing, or manual editing behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

REPOSITORY = Path(__file__).resolve().parents[1]
EMU_PER_PIXEL = 9525
TOLERANCE = 0.002
NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
OPCODES = {'moveTo': 'moveTo', 'lineTo': 'lnTo', 'cubicBezTo': 'cubicBezTo',
           'quadBezTo': 'quadBezTo', 'close': 'close'}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPOSITORY))
    except ValueError:
        return str(path)


def normalized_text(value: str) -> str:
    # The exporter expands compatibility ligatures, e.g. ﬁ -> fi.
    return unicodedata.normalize('NFKC', value).replace('\r', '').replace('\n', '').strip()


def geometry(element: ET.Element) -> list[float]:
    transform = element.find('p:spPr/a:xfrm', NS)
    offset, extent = transform.find('a:off', NS), transform.find('a:ext', NS)
    return [float(offset.get('x')) / EMU_PER_PIXEL,
            float(offset.get('y')) / EMU_PER_PIXEL,
            float(extent.get('cx')) / EMU_PER_PIXEL,
            float(extent.get('cy')) / EMU_PER_PIXEL,
            float(transform.get('rot', '0')) / 60000]


def rotation_delta(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def transform_matches(actual: list[float], expected: list[float]) -> bool:
    return (max(abs(a - b) for a, b in zip(actual[:4], expected[:4])) <= TOLERANCE
            and rotation_delta(actual[4], expected[4]) <= TOLERANCE)


def audit(folder: Path) -> dict:
    source = json.loads((folder / 'sources.json').read_text())['papers'][0]
    # Bundles document paths relative to output/<slug>, including staged bundles.
    scene_path = REPOSITORY / source['diagram_json'].removeprefix('../../')
    scene_bytes = scene_path.read_bytes()
    scene = json.loads(scene_bytes)
    pptx_path = folder / source['editable_pptx']
    pptx_bytes = pptx_path.read_bytes()
    errors: list[str] = []
    counts = dict(scene_nodes=len(scene['nodes']), named_shapes_checked=0,
                  text_labels_checked=0, paths_checked=0,
                  curve_commands_checked=0, images_checked=0,
                  semantic_connectors_not_geometry_checked=len(scene.get('edges', [])))
    max_position = max_path = 0.0
    with zipfile.ZipFile(pptx_path) as archive:
        slide = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
        size = ET.fromstring(archive.read('ppt/presentation.xml')).find('p:sldSz', NS)
        wanted_canvas = [scene['canvas']['width'] * EMU_PER_PIXEL,
                         scene['canvas']['height'] * EMU_PER_PIXEL]
        actual_canvas = [float(size.get('cx')), float(size.get('cy'))]
        if max(abs(a - b) for a, b in zip(wanted_canvas, actual_canvas)) > 1:
            errors.append('Canvas dimensions differ')
        shapes = {}
        for shape in slide.findall('.//p:sp', NS):
            name = shape.find('p:nvSpPr/p:cNvPr', NS).get('name')
            if name in shapes:
                errors.append(f'{name}: duplicate named shape')
            shapes[name] = shape
        relations = {}
        for relation in ET.fromstring(archive.read('ppt/slides/_rels/slide1.xml.rels')):
            target = relation.get('Target')
            relations[relation.get('Id')] = posixpath.normpath(
                target.lstrip('/') if target.startswith('/') else 'ppt/slides/' + target)
        pictures = []
        for picture in slide.findall('.//p:pic', NS):
            rid = picture.find('p:blipFill/a:blip', NS).get('{' + NS['r'] + '}embed')
            pictures.append((sha256(archive.read(relations[rid])), geometry(picture)))
        for node in scene['nodes']:
            identifier = node['id']
            shape = shapes.get(identifier)
            if shape is None:
                errors.append(f'{identifier}: missing named shape')
                continue
            counts['named_shapes_checked'] += 1
            actual = geometry(shape)
            expected = [node[k] for k in ('x', 'y', 'width', 'height')] + [node.get('rotation', 0)]
            max_position = max(max_position, max(abs(a - b) for a, b in zip(actual[:4], expected[:4])))
            if not transform_matches(actual, expected):
                errors.append(f'{identifier}: transform mismatch')
            if node['shape'] == 'image':
                asset_hash = sha256((scene_path.parent / node['asset']).read_bytes())
                if any(ph == asset_hash and transform_matches(pg, expected) for ph, pg in pictures):
                    counts['images_checked'] += 1
                else:
                    errors.append(f'{identifier}: image bytes/placement mismatch')
            elif node['shape'] != 'path':
                label = node.get('label', '')
                actual_text = ''.join(e.text or '' for e in shape.findall('.//a:t', NS))
                if normalized_text(label) != normalized_text(actual_text):
                    errors.append(f'{identifier}: native text differs {label!r} versus {actual_text!r}')
                if label.strip():
                    counts['text_labels_checked'] += 1
            else:
                paths = shape.findall('p:spPr/a:custGeom/a:pathLst/a:path', NS)
                if len(paths) != 1:
                    errors.append(f'{identifier}: expected one custom path')
                    continue
                path = paths[0]
                commands = list(path)
                source_commands = node['commands']
                counts['paths_checked'] += 1
                if len(commands) != len(source_commands):
                    errors.append(f'{identifier}: path command count differs')
                    continue
                for command, source_command in zip(commands, source_commands):
                    operation, values = next(iter(source_command.items()))
                    if command.tag.rsplit('}', 1)[-1] != OPCODES[operation]:
                        errors.append(f'{identifier}: path opcode mismatch')
                        continue
                    if operation == 'close':
                        continue
                    expected_points = []
                    if operation in ('cubicBezTo', 'quadBezTo'):
                        expected_points.append([values['x1'], values['y1']])
                    if operation == 'cubicBezTo':
                        expected_points.append([values['x2'], values['y2']])
                    expected_points.append([values['x'], values['y']])
                    points = command.findall('a:pt', NS)
                    if len(points) != len(expected_points):
                        errors.append(f'{identifier}: path point count differs')
                        continue
                    for point, expected_point in zip(points, expected_points):
                        # Scale from custom-path coordinate space to scene pixels.
                        ax = float(point.get('x')) * node['width'] / float(path.get('w'))
                        ay = float(point.get('y')) * node['height'] / float(path.get('h'))
                        delta = max(abs(ax - expected_point[0]), abs(ay - expected_point[1]))
                        max_path = max(max_path, delta)
                        if delta > TOLERANCE:
                            errors.append(f'{identifier}: path point differs')
                            break
                    if operation in ('cubicBezTo', 'quadBezTo'):
                        counts['curve_commands_checked'] += 1
    return {
        'folder': relative(folder), 'diagram_id': scene['id'],
        'scene_sha256': sha256(scene_bytes), 'pptx_sha256': sha256(pptx_bytes),
        'status': 'passed' if not errors else 'needs investigation', 'checks': counts,
        'maximum_object_position_delta_scene_pixels': round(max_position, 8),
        'maximum_path_control_point_delta_scene_pixels': round(max_path, 8),
        'tolerance_scene_pixels': TOLERANCE, 'errors': errors[:100], 'error_count': len(errors),
        'text_normalization': 'Unicode NFKC normalizes compatibility ligatures; CR/LF ignored',
        'limitation': 'OOXML semantic/coordinate consistency is not an application-render or '
                      'text-layout check; font substitution, glyph appearance, visual clipping, '
                      'semantic connector routing and editing UX are not validated.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folders', nargs='*', help='Bundle folders, repository-relative or absolute')
    parser.add_argument('--output-dir', default='build/ooxml_geometry_qa', help='Report folder, repository-relative or absolute')
    args = parser.parse_args()
    folders = [REPOSITORY / f for f in args.folders] if args.folders else sorted(
        p for p in (REPOSITORY / 'output').iterdir() if (p / 'sources.json').is_file())
    output = REPOSITORY / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for folder in folders:
        try:
            result = audit(folder.resolve())
        except Exception as error:
            result = {'folder': relative(folder), 'status': 'error', 'error': repr(error)}
        results.append(result)
        (output / (folder.name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    (output / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
    counts = Counter(result['status'] for result in results)
    print(json.dumps({'bundles': len(results), 'statuses': dict(counts), 'reports': relative(output)}, indent=2))
    for result in results:
        if result['status'] != 'passed':
            print(json.dumps(result))
    return 0 if results and all(r['status'] == 'passed' for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
