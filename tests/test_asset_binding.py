import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from paper_figure.exporters import export, drawio, input_hashes
from paper_figure.model import ValidationError
ROOT=Path(__file__).resolve().parents[1]

class AssetBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.scene=json.loads((ROOT/'examples/minimal.json').read_text())
        self.scene['nodes'].append(dict(id='picture',shape='image',asset='pixel.png',alt='fixture',x=0,y=0,width=20,height=20))
        self.source=self.root/'scene.json';self.source.write_text(json.dumps(self.scene))
        self.asset=self.root/'pixel.png'
        self.asset.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl1sAAAAASUVORK5CYII='))
    def test_manifest_records_raster_bytes(self):
        m=export(self.scene,self.source,self.root/'out',('drawio',))
        self.assertEqual(m['assets'],input_hashes(self.scene,self.source)['assets'])
        self.assertEqual(m['assets'][0]['name'],'pixel.png')
    def test_asset_change_during_export_preserves_previous_output(self):
        out=self.root/'out';out.mkdir();existing=out/(self.scene['id']+'.drawio');existing.write_bytes(b'previous')
        def mutate(scene,target,base):
            drawio(scene,target,base);self.asset.write_bytes(self.asset.read_bytes()+b'\n')
        with patch('paper_figure.exporters.drawio',side_effect=mutate):
            with self.assertRaises(ValidationError):export(self.scene,self.source,out,('drawio',),force=True)
        self.assertEqual(existing.read_bytes(),b'previous')
    def test_json_change_during_export_refused(self):
        def mutate(scene,target,base):
            drawio(scene,target,base);self.source.write_text(self.source.read_text()+'\n')
        with patch('paper_figure.exporters.drawio',side_effect=mutate):
            with self.assertRaises(ValidationError):export(self.scene,self.source,self.root/'out',('drawio',))
        self.assertFalse((self.root/'out'/(self.scene['id']+'.drawio')).exists())

    def test_changed_source_before_export_refused(self):
        changed=json.loads(self.source.read_text());changed['title']='Different source'
        self.source.write_text(json.dumps(changed))
        with self.assertRaises(ValidationError):export(self.scene,self.source,self.root/'out',('drawio',))
        self.assertFalse((self.root/'out').exists())
    def test_mismatched_memory_before_export_refused(self):
        self.scene['title']='Changed in memory'
        with self.assertRaises(ValidationError):export(self.scene,self.source,self.root/'out',('drawio',))
        self.assertFalse((self.root/'out').exists())
