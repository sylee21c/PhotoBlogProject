"""Verify private deploy output and rerun behavior without touching an account."""
import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('cloud_config',ROOT/'PhotoBlogServer/deploy/configure_pythonanywhere.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class CloudConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name);(self.root/'PhotoBlogServer').mkdir();(self.root/'PhotoBlogServer/manage.py').touch()

    def test_private_wsgi_is_valid_and_does_not_embed_secret(self):
        result=module.configure(self.root,'student-demo.pythonanywhere.com')
        secret=json.loads((self.root/'.runtime/cloud-secrets.json').read_text())['DJANGO_SECRET_KEY']
        source=Path(result['wsgi_source']).read_text();compile(source,'generated_wsgi.py','exec')
        self.assertNotIn(secret,source);self.assertNotIn(secret,json.dumps(result));self.assertIn('DJANGO_DEBUG',source)

    def test_rerun_retains_secret_and_can_update_domain(self):
        module.configure(self.root,'one.pythonanywhere.com');before=(self.root/'.runtime/cloud-secrets.json').read_bytes()
        result=module.configure(self.root,'two.eu.pythonanywhere.com')
        self.assertEqual((self.root/'.runtime/cloud-secrets.json').read_bytes(),before)
        self.assertIn('two.eu.pythonanywhere.com',Path(result['wsgi_source']).read_text())

    def test_bad_domain_creates_no_private_configuration(self):
        for value in ['https://user.pythonanywhere.com','a.example.org','user.pythonanywhere.com/path','x\nBAD']:
            with self.assertRaises(ValueError):module.configure(self.root,value)
        self.assertFalse((self.root/'.runtime').exists())

    def test_wrong_project_root_is_rejected(self):
        with self.assertRaises(ValueError):module.configure(self.root/'missing','one.pythonanywhere.com')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CloudConfigurationTests))
    (ROOT/'evidence/deployment-config-tests.json').write_text(json.dumps({'tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors)},indent=2),encoding='utf-8')
    sys.exit(not result.wasSuccessful())
