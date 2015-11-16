#!/usr/bin/env python

import unittest
import sys

from env import ABSPATH
import pyneuronjs.module as module


class TestModuleParser(unittest.TestCase):

    def test_parse_module_id_name(self):
        id = 'jquery'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, 'jquery')
        self.assertEqual(version, '*')
        self.assertEqual(path, '')

    def test_parse_module_id_name_version(self):
        id = 'jquery@1.0.0'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, 'jquery')
        self.assertEqual(version, '1.0.0')
        self.assertEqual(path, '')

    def test_parse_module_id_name_version_path(self):
        id = 'jquery@1.0.0/a.js'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, 'jquery')
        self.assertEqual(version, '1.0.0')
        self.assertEqual(path, '/a.js')

        id = 'jquery@1.0.0/'
        (name, version, path) = module.parse_module_id(id)

        self.assertEqual(name, 'jquery')
        self.assertEqual(version, '1.0.0')
        self.assertEqual(path, '')

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
