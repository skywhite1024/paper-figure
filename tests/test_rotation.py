import copy
import os
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from paper_figure.model import load,validate,ValidationError
from paper_figure.exporters import export
ROOT=Path(__file__).resolve().parents[1]
class RotationTests(unittest.TestCase):
    def setUp(self):
        self.scene=load(ROOT/'examples/minimal.json')
        self.scene['nodes'][0].update(shape='text',label='Environment',x=-20,y=80,width=120,height=20,rotation=90,no_wrap=True,font_size=16)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
    def test_rotated_visible_bounds_allow_negative_unrotated_frame(self):validate(self.scene)
    def test_rotated_visible_bounds_still_enforced(self):
        self.scene['nodes'][0]['x']=-100
        with self.assertRaises(ValidationError):validate(self.scene)
    def test_invalid_rotation_rejected(self):
        for value in [True, float('nan'),361,'90']:
            self.scene['nodes'][0]['rotation']=value
            with self.assertRaises(ValidationError):validate(self.scene)
    def test_drawio_rotation_property(self):
        export(self.scene,ROOT/'examples/minimal.json',self.out,('drawio',))
        root=ET.parse(self.out/'demo.drawio');self.assertIn('rotation=90;',root.find('.//mxCell[@id="a"]').get('style'))
    @unittest.skipUnless(os.getenv('PAPER_FIGURE_TEST_PPTX')=='1','optional Artifact Tool integration')
    def test_pptx_native_text_rotation_and_preview(self):
        export(self.scene,ROOT/'examples/minimal.json',self.out,('pptx',),preview=True)
        with zipfile.ZipFile(self.out/'demo.pptx') as z:
            root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
            self.assertTrue(any(e.get('rot')=='5400000' for e in root.iter() if e.tag.endswith('xfrm')))
            self.assertIn('Environment',''.join(e.text or '' for e in root.iter() if e.tag.endswith('}t')))
        self.assertTrue((self.out/'demo.png').stat().st_size>100)
