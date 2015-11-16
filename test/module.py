#!/usr/bin/env python

import unittest
import sys

from env import ABSPATH
import pyneuronjs.module as module


class TestModuleParser(unittest.TestCase):

    def test_parse_module_id_name(self):
        id = b'jquery'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, b'jquery')
        self.assertEqual(version, b'*')
        self.assertEqual(path, b'')

    def test_parse_module_id_name_version(self):
        id = b'jquery@1.0.0'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, b'jquery')
        self.assertEqual(version, b'1.0.0')
        self.assertEqual(path, b'')

    def test_parse_module_id_name_version_path(self):
        id = b'jquery@1.0.0/a.js'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, b'jquery')
        self.assertEqual(version, b'1.0.0')
        self.assertEqual(path, b'/a.js')

        id = b'jquery@1.0.0/'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, b'jquery')
        self.assertEqual(version, b'1.0.0')
        self.assertEqual(path, b'')

    def test_module_id(self):
        id = module.module_id('jquery', '*')
        self.assertEqual(id, 'jquery@*/jquery.js')

        id = module.module_id('jquery', '*', '')
        self.assertEqual(id, 'jquery@*/jquery.js')

        id = module.module_id('jquery', '*', '/')
        self.assertEqual(id, 'jquery@*/jquery.js')

        id = module.module_id('jquery', '*', '/a.js')
        self.assertEqual(id, 'jquery@*/a.js')

        id = module.module_id('jquery', '1.1.0', '/a.js')
        self.assertEqual(id, 'jquery@1.1.0/a.js')


suite = unittest.TestLoader().loadTestsFromTestCase(TestModuleParser)
runner = unittest.TextTestRunner(verbosity=2).run(suite)

exit_code = 0 if runner.wasSuccessful() else 1
sys.exit(exit_code)
