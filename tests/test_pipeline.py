import base64,copy,json,os,tempfile,unittest,xml.etree.ElementTree as ET,zipfile,zlib
from pathlib import Path
from urllib.parse import unquote
from paper_figure.model import load,validate,ValidationError,local_asset,metrics
from paper_figure.exporters import export,stencil
from paper_figure.cli import batch,main
ROOT=Path(__file__).resolve().parents[1]
class PipelineTests(unittest.TestCase):
 def setUp(self):
  self.d=load(ROOT/'examples/minimal.json');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
 def invalid(self,fn):
  fn(self.d)
  with self.assertRaises(ValidationError):validate(self.d)
 def test_valid(self):self.assertEqual(metrics(self.d)['native_freeform_paths'],1)
 def test_negative(self):self.invalid(lambda d:d['nodes'][0].update(x=-1))
 def test_nan(self):self.invalid(lambda d:d['nodes'][0].update(width=float('nan')))
 def test_bool_geometry(self):self.invalid(lambda d:d['nodes'][0].update(x=True))
 def test_duplicate(self):self.invalid(lambda d:d['nodes'][1].update(id='a'))
 def test_reserved(self):self.invalid(lambda d:d['nodes'][0].update(id='0'))
 def test_unhashable_shape(self):self.invalid(lambda d:d['nodes'][0].update(shape=[]))
 def test_unhashable_endpoint(self):self.invalid(lambda d:d['edges'][0].update(source=[]))
 def test_unhashable_status(self):self.invalid(lambda d:d['provenance'].update(status=[]))
 def test_out_of_canvas(self):self.invalid(lambda d:d['nodes'][0].update(x=599))
 def test_xml_control(self):self.invalid(lambda d:d['nodes'][0].update(label='bad\x00label'))
 def test_color_style_injection(self):self.invalid(lambda d:d['edges'][0].update(stroke='#000000;html=1'))
 def test_font_style_injection(self):self.invalid(lambda d:d['nodes'][0].update(font_family='Arial;html=1'))
 def test_bad_dash(self):self.invalid(lambda d:d['edges'][0].update(dash='true'))
 def test_bad_path(self):self.invalid(lambda d:d['nodes'][2]['commands'].append({'script':{}}))
 def test_bad_path_nan(self):self.invalid(lambda d:d['nodes'][2]['commands'][0]['moveTo'].update(x=float('nan')))
 def test_asset_escape(self):
  with self.assertRaises(ValidationError):local_asset(self.out,'../secret.png')
 def test_asset_absolute(self):
  with self.assertRaises(ValidationError):local_asset(self.out,'/tmp/secret.png')
 def test_source_page_required(self):self.invalid(lambda d:d['provenance'].update(status='figure_recreation'))
 def test_drawio_native(self):
  export(self.d,ROOT/'examples/minimal.json',self.out,('drawio',));r=ET.parse(self.out/'demo.drawio');self.assertEqual(len(r.findall('.//mxCell[@vertex="1"]')),3);self.assertEqual(len(r.findall('.//mxCell[@edge="1"]')),1)
 def test_stencil_codec_and_endpoints(self):
  n=copy.deepcopy(self.d['nodes'][2]);n['id']='curve%中文';n['commands'].append({'quadBezTo':{'x1':2,'y1':3,'x':4,'y':5}});s=ET.fromstring(unquote(zlib.decompress(base64.b64decode(stencil(n)),-15).decode()));self.assertEqual(s.get('name'),n['id']);self.assertEqual(s.find('.//curve').get('x3'),'220');self.assertEqual(s.find('.//quad').get('y2'),'5')
 def test_overwrite(self):
  export(self.d,ROOT/'examples/minimal.json',self.out,('drawio',))
  with self.assertRaises(ValidationError):export(self.d,ROOT/'examples/minimal.json',self.out,('drawio',))
 def test_batch_status(self):
  c={'schema_version':1,'papers':[{'id':'todo','title':'Todo','url':'https://example.org','status':'not_reviewed'},{'id':'bad','title':'Bad','url':'https://example.org','status':'recreated','diagram':'missing.json'}]};p=self.out/'catalog.json';p.write_text(json.dumps(c));r=batch(p,self.out/'out',('drawio',));self.assertEqual(len(r['skipped']),1);self.assertEqual(len(r['failed']),1)
 def test_cli_bad(self):self.assertEqual(main(['validate',str(self.out/'missing')]),2)
 @unittest.skipUnless(os.getenv('PAPER_FIGURE_TEST_PPTX')=='1','optional Artifact Tool integration')
 def test_pptx_native_paths_connectors(self):
  export(self.d,ROOT/'examples/minimal.json',self.out,('pptx',));ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
  with zipfile.ZipFile(self.out/'demo.pptx') as z:
   r=ET.fromstring(z.read('ppt/slides/slide1.xml'));self.assertEqual(len(r.findall('.//a:custGeom',ns)),1);self.assertEqual(len(r.findall('.//p:cxnSp',ns)),1);self.assertEqual(len(r.findall('.//a:stCxn',ns)),1);self.assertEqual(len(r.findall('.//a:cubicBezTo',ns)),1);self.assertIn(b'paper_url',z.read('ppt/notesSlides/notesSlide1.xml'))
 def test_freeform_label_cannot_silently_disappear(self):
  node=next(n for n in self.d['nodes'] if n['shape']=='path');node['label']='Visible label'
  with self.assertRaises(ValidationError):validate(self.d)
 def test_drawio_honors_no_wrap_and_text_inset(self):
  self.d['nodes'][0].update(no_wrap=True,text_inset=3)
  source=self.out/'scene.json';source.write_text(json.dumps(self.d))
  export(self.d,source,self.out,('drawio',))
  doc=ET.parse(self.out/(self.d['id']+'.drawio'))
  cell=doc.find('.//mxCell[@id="a"]')
  self.assertIn('whiteSpace=nowrap;',cell.get('style'))
  self.assertIn('spacing=3;',cell.get('style'))

if __name__=='__main__':unittest.main()
