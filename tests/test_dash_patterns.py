import copy
import io
import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

try:
    import fitz
except ImportError:
    fitz = None

from paper_figure.exporters import drawio, export
from paper_figure.model import ValidationError, load, validate
from paper_figure.pdf_extract import extract, source_dash

ROOT = Path(__file__).resolve().parents[1]


class DashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scene = load(ROOT / 'examples/minimal.json')

    def test_source_dot_longdash_and_composite_presets(self):
        cases = [('[1 3] 0', 'dotted', [2, 6]), ('[12 3] 0', 'dashed', [24, 6]),
                 ('[6 2 1 2] 1', 'dash-dot', [12, 4, 2, 4]),
                 ('[6 2 1 2 1 2] 0', 'dash-dot-dot', [12, 4, 2, 4, 2, 4])]
        for raw, style, pattern in cases:
            with self.subTest(raw=raw):
                parsed = source_dash(raw, 2, 2)
                self.assertEqual(parsed['dash_style'], style)
                self.assertEqual(parsed['dash_pattern'], pattern)
                self.assertEqual(parsed['source_dash'], raw)
                self.assertIn('not exact', parsed['dash_approximation'])
        self.assertEqual(source_dash('[6 2 1 2] 1', 2, 2)['dash_phase'], 2)

    def test_solid_odd_array_and_zero_length_dots(self):
        self.assertFalse(source_dash('[] 0', 1, 1)['dash'])
        self.assertEqual(source_dash('[3] 0', 1, 1)['dash_pattern'], [3, 3])
        self.assertEqual(source_dash('[0 3] 0', 1, 1)['dash_pattern'], [.001, 3])
        self.assertEqual(source_dash('[0 3] 0', 1, 1)['dash_style'], 'dotted')

    def test_raw_dash_syntax_negative_nonfinite_and_injection_rejected(self):
        for value in ('[NaN 2] 0', '[1e999 2] 0', '[-1 2] 0', '[1 2] -1', '[0 0] 0',
                      '[1;html=1 2] 0', '[1.2.3] 0', '[1,2] 0', 'arbitrary', [], '[1 2] nan'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                source_dash(value, 1, 1)

    def test_model_rejects_unsafe_or_ambiguous_dash_fields_on_nodes_and_edges(self):
        variants = [{'dash_style': 'dotted;html=1'}, {'dash_style': []}, {'dash_style': 'longDash'},
                    {'dash_pattern': [1, '2;html=1']}, {'dash_pattern': [1, float('nan')]},
                    {'dash_pattern': [1, float('inf')]}, {'dash_pattern': [1, 0]},
                    {'dash_pattern': [1, -2]}, {'dash_pattern': [1, True]}, {'dash_pattern': [1]},
                    {'dash_pattern': [1, 2], 'dash': False}, {'dash_style': 'solid', 'dash': True},
                    {'dash_pattern': [1, 2], 'dash_style': 'solid'}, {'dash_phase': 1},
                    {'dash_pattern': [1, 2], 'dash_phase': -1}]
        for bucket in ('nodes', 'edges'):
            for fields in variants:
                with self.subTest(bucket=bucket, fields=fields):
                    scene = copy.deepcopy(self.scene)
                    scene[bucket][0].update(fields)
                    with self.assertRaises(ValidationError):
                        validate(scene)

    def test_drawio_uses_scaled_pattern_for_paths_and_connectors(self):
        self.scene['nodes'][2].update(dash=True, dash_style='dotted', dash_pattern=[2, 6], stroke_width=4)
        self.scene['edges'][0].update(dash=True, dash_style='dashed', dash_pattern=[24, 6], stroke_width=4)
        validate(self.scene)
        output = self.root / 'dash.drawio'
        drawio(self.scene, output, ROOT / 'examples')
        doc = ET.parse(output)
        node = doc.find('.//mxCell[@id="' + self.scene['nodes'][2]['id'] + '"]')
        edge = doc.find('.//mxCell[@edge="1"]')
        self.assertIn('dashed=1;dashPattern=0.5 1.5;', node.get('style'))
        self.assertIn('dashed=1;dashPattern=6 1.5;', edge.get('style'))

    def test_drawio_style_only_presets_and_legacy_boolean(self):
        for style, expected in [('dotted', '1 1'), ('dash-dot', '3 2 1 2'), ('dash-dot-dot', '3 2 1 2 1 2')]:
            scene = copy.deepcopy(self.scene)
            scene['nodes'][0].update(dash_style=style)
            output = self.root / (style + '.drawio')
            drawio(scene, output, ROOT / 'examples')
            self.assertIn('dashPattern=' + expected + ';', ET.parse(output).find('.//mxCell[@id="a"]').get('style'))
        scene = copy.deepcopy(self.scene)
        scene['nodes'][0]['dash'] = True
        validate(scene)
        drawio(scene, self.root / 'legacy.drawio', ROOT / 'examples')
        self.assertIn('dashed=1;', ET.parse(self.root / 'legacy.drawio').find('.//mxCell[@id="a"]').get('style'))

    @unittest.skipUnless(fitz, 'optional PyMuPDF dependency unavailable')
    def test_synthetic_pdf_extraction_preserves_scaled_raw_patterns(self):
        document = fitz.open()
        page = document.new_page(width=300, height=200)
        page.draw_line((20, 40), (250, 40), width=2, color=(0, 0, 0), dashes='[1 3] 0')
        page.draw_line((20, 80), (250, 80), width=2, color=(0, 0, 0), dashes='[12 3] 1')
        pdf = self.root / 'dashes.pdf'
        document.save(pdf)
        document.close()
        config = {'id': 'dash-fixture', 'paper_title': 'Dash fixture', 'paper_url': 'https://example.org',
                  'figure': 'Figure 1', 'page': 1, 'crop': [0, 0, 300, 200], 'scale': 2,
                  'license': 'Synthetic fixture', 'notes': 'Tests only'}
        scene = extract(pdf, config, self.root / 'extracted')
        paths = [node for node in scene['nodes'] if node['shape'] == 'path']
        self.assertEqual(paths[0]['dash_style'], 'dotted')
        self.assertEqual(paths[0]['dash_pattern'], [2, 6])
        self.assertEqual(paths[1]['dash_pattern'], [24, 6])
        self.assertEqual(paths[1]['dash_phase'], 2)
        self.assertIn('not exact', scene['provenance']['dash_fidelity'])
        self.assertFalse(any(node['shape'] == 'image' for node in scene['nodes']))

    @unittest.skipUnless(fitz, 'optional PyMuPDF dependency unavailable')
    def test_raw_image_with_existing_alpha_and_separate_mask(self):
        from PIL import Image
        image = Image.new('RGBA', (20, 20), (255, 0, 0, 90))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        document = fitz.open()
        page = document.new_page(width=300, height=200)
        page.draw_line((10, 10), (200, 10), color=(0, 0, 0), width=1)
        page.insert_image(fitz.Rect(20, 20, 80, 80), stream=image_bytes.getvalue())
        pdf = self.root / 'alpha.pdf'
        document.save(pdf)
        document.close()
        original = fitz.Page.get_text
        def with_existing_alpha(page, option='text', *args, **kwargs):
            result = original(page, option, *args, **kwargs)
            if option == 'dict':
                for block in result['blocks']:
                    if block['type'] == 1:
                        self.assertTrue(block.get('mask'))
                        block['image'] = image_bytes.getvalue()
            return result
        config = {'id': 'alpha-fixture', 'paper_title': 'Alpha fixture', 'paper_url': 'https://example.org',
                  'figure': 'Figure 1', 'page': 1, 'crop': [0, 0, 300, 200], 'scale': 1,
                  'license': 'Synthetic fixture', 'notes': 'Tests only', 'reviewed_raw_images': [0]}
        with patch.object(fitz.Page, 'get_text', with_existing_alpha):
            scene = extract(pdf, config, self.root / 'alpha-extracted')
        self.assertEqual(sum(node['shape'] == 'image' for node in scene['nodes']), 1)
        restored = Image.open(self.root / 'alpha-extracted/alpha-fixture-source-image-0.png').convert('RGBA')
        self.assertEqual(restored.getpixel((10, 10))[3], 90)

    @unittest.skipUnless(os.getenv('CODEX_PRIMARY_RUNTIME_NODE_MODULES') and os.getenv('CODEX_PRIMARY_RUNTIME_NODE'),
                         'optional Artifact Tool runtime unavailable')
    def test_native_pptx_presets_and_preview_agree(self):
        from PIL import Image
        styles = ['dotted', 'dashed', 'dash-dot', 'dash-dot-dot']
        scene = {'schema_version': 1, 'id': 'dash-native', 'title': 'Native dash fixture',
                 'canvas': {'width': 600, 'height': 300}, 'provenance': copy.deepcopy(self.scene['provenance']),
                 'nodes': [], 'edges': []}
        for index, style in enumerate(styles):
            scene['nodes'].append({'id': style, 'shape': 'path', 'x': 30, 'y': 40 + index * 50,
                'width': 500, 'height': 1, 'fill': 'none', 'stroke': '#000000', 'stroke_width': 4,
                'dash_style': style, 'commands': [{'moveTo': {'x': 0, 'y': .5}}, {'lineTo': {'x': 500, 'y': .5}}]})
        scene['edges'] = [{'id': 'dotted-edge', 'source': 'dotted', 'target': 'dashed', 'dash_style': 'dotted', 'arrow': False}]
        validate(scene)
        source = self.root / 'native.json'
        source.write_text(json.dumps(scene))
        export(scene, source, self.root / 'native', ('pptx', 'drawio'), preview=True)
        ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
              'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(self.root / 'native/dash-native.pptx') as archive:
            document = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            presets = {shape.find('.//p:cNvPr', ns).get('name'): shape.find('.//a:prstDash', ns).get('val')
                       for shape in document.findall('.//p:sp', ns)}
            self.assertEqual(presets, {'dotted': 'dot', 'dashed': 'dash', 'dash-dot': 'dashDot', 'dash-dot-dot': 'lgDashDotDot'})
            self.assertEqual(document.find('.//p:cxnSp//a:prstDash', ns).get('val'), 'dot')
            self.assertEqual(len(document.findall('.//a:custGeom', ns)), 4)
            self.assertFalse(document.findall('.//p:pic', ns))
        preview = Image.open(self.root / 'native/dash-native.png').convert('RGB')
        def runs(y):
            lengths, current = [], 0
            for x in range(60, 450):
                if max(preview.getpixel((x, y))) < 100:
                    current += 1
                elif current:
                    lengths.append(current)
                    current = 0
            return sorted(lengths)
        dots, dashes = runs(40), runs(90)
        self.assertGreater(len(dots), 10)
        self.assertGreater(len(dashes), 5)
        self.assertLess(dots[len(dots)//2], dashes[len(dashes)//2])


if __name__ == '__main__':
    unittest.main()
