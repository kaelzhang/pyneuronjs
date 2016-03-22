#!/usr/bin/env python


import unittest
import sys
import json
import os

from env import ABSPATH
from neuronjs.walker import Walker


def read_json(filename):
    filename = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
    content = open(filename).read()
    return json.loads(content)

def get_result(facades):
    json = read_json('dependency.json')
    walker = Walker(tree=json)
    return walker.look_up(facades)


class TestWalker(unittest.TestCase):
    def test_no_dependency(self):
        packages, graph = get_result(['a'])
        self.assertEqual(packages, {
                'a': set([('*', '')])
            })
        self.assertEqual(graph['_'], {
                'a@*': 0
            })

    def test_multiple_dependency_version(self):
        packages, graph = get_result(['home'])
        self.assertEqual(len(packages.get('c')), 2)

    def test_cyclic_dependency(self):
        packages, graph = get_result(['d@2.3.0'])
        self.assertEqual(packages.get('d'), set([('2.3.0', '')]))
        self.assertEqual(packages.get('e'), set([('1.0.0', '')]))

    def test_duplicate_dependencies(self):
        packages, graph = get_result(['home'])
        packages2, graph2 = get_result(['home2', 'home'])
        self.assertEqual(packages.get('b'), packages2.get('b'))
        self.assertEqual(packages.get('c'), packages2.get('c'))

    def test_multiple_entries(self):
        packages, graph = get_result(['home/a.js', 'home/b.js'])
        self.assertEqual(len(packages.get('home')), 2)

        expected = [('*', '/a.js'), ('*', '/b.js')]
        expected.sort()

        result = list(packages.get('home'))
        result.sort()

        self.assertEqual(expected, result)


suite = unittest.TestLoader().loadTestsFromTestCase(TestWalker)
runner = unittest.TextTestRunner(verbosity=2).run(suite)

exit_code = 0 if runner.wasSuccessful() else 1
sys.exit(exit_code)
