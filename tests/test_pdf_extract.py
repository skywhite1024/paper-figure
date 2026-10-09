import json
import tempfile
import unittest
from pathlib import Path
try:
    import fitz
except ImportError:
    fitz = None
from paper_figure.pdf_extract import extract
from paper_figure.model import ValidationError

@unittest.skipUnless(fitz, 'optional PyMuPDF dependency unavailable')
class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        doc = fitz.open(); page = doc.new_page(width=300, height=200)
        page.draw_rect(fitz.Rect(20, 20, 120, 100), color=(0, 0, 1), fill=(.9, .9, 1))
        page.insert_text((30, 60), 'Editable module', fontsize=10)
        self.pdf = self.root/'source.pdf'; doc.save(self.pdf); doc.close()
        self.config = dict(id='test-figure', paper_title='Test', paper_url='https://example.org/paper',
                           figure='Figure 1', page=1, crop=[10, 10, 290, 180], license='Test fixture', notes='Synthetic test only')
    def test_extract_native_paths_and_text(self):
        scene = extract(self.pdf, self.config, self.root/'scene')
        self.assertTrue(any(n['shape']=='path' for n in scene['nodes']))
        self.assertTrue(any(n.get('label')=='Editable module' for n in scene['nodes']))
        self.assertEqual(scene['provenance']['extraction_warnings'], [])
        self.assertIn('pending', scene['provenance']['extraction_review'])
    def test_reject_outside_page(self):
        self.config['crop']=[0, 0, 400, 200]
        with self.assertRaises(ValidationError): extract(self.pdf, self.config, self.root/'scene')
    def test_reject_full_image_backdrop(self):
        self.config['raster_regions']=[{'bbox':self.config['crop'], 'reason':'Everything'}]
        with self.assertRaises(ValidationError): extract(self.pdf, self.config, self.root/'scene')
    def test_raster_region_removes_duplicate_text(self):
        self.config['raster_regions']=[{'bbox':[19,19,121,101], 'reason':'source inset test'}]
        # Add another native node so extraction remains a mixed editable diagram.
        doc=fitz.open(self.pdf); doc[0].insert_text((150,130),'Outside inset', fontsize=10)
        other=self.root/'other.pdf'; doc.save(other); doc.close()
        scene=extract(other,self.config,self.root/'scene')
        self.assertFalse(any(n.get('label')=='Editable module' for n in scene['nodes']))
        self.assertEqual(sum(n['shape']=='image' for n in scene['nodes']),1)

    def test_unsafe_id_rejected_before_image_writes(self):
        self.config['id']='../escaped'
        self.config['raster_regions']=[{'bbox':[19,19,121,101], 'reason':'test inset'}]
        with self.assertRaises(ValidationError): extract(self.pdf,self.config,self.root/'scene')
        self.assertFalse((self.root/'escaped-raster-0.png').exists())
    def test_combined_raster_coverage_rejected(self):
        self.config['raster_regions']=[{'bbox':[10,10,150,180], 'reason':'left'}, {'bbox':[150,10,290,180], 'reason':'right'}]
        with self.assertRaises(ValidationError): extract(self.pdf,self.config,self.root/'scene')
    def test_selected_font_preserved_as_outline_paths(self):
        self.config['outline_fonts']=['Helvetica']
        scene=extract(self.pdf,self.config,self.root/'scene')
        self.assertFalse(any(n['shape']=='text' for n in scene['nodes']))
        self.assertGreater(sum(n['shape']=='path' for n in scene['nodes']),1)
        self.assertIn('outlined_math_limit',scene['provenance'])
