from env import ABSPATH
import os
import json

from pyneuron import Neuron

dependency_tree = {}

dependency_file = os.path.normpath(
  os.path.join(ABSPATH, './test/fixtures/dependency.json')
)

try:
  dependency_json = open(dependency_file).read()
  dependency_tree = json.loads(dependency_json)
except Exception, e:
  print e

version = dependency_tree.get('_version')

# unset `dependency_file` which might leak the file structure of server
dependency_file = None

def resolve(module_ids):
  if type(module_ids) is not list:
    return _resolve(module_ids)

  module_ids = [
    _resolve(i)
    for i in module_ids
  ]

  return '/concat' + ','.join(module_ids)

def _resolve(module_id):
  return '/mod' + '/' + module_id.replace('@', '/')

nr = Neuron(
  version=version,
  dependency_tree=dependency_tree,
  resolve=resolve,
  path='mod',
  debug=True,
  js_config={
    'path': 'http://localhost:8000/mod'
  }
)

nr.facade('home')
nr.combo()

print nr.output()
