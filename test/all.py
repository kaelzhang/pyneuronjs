#

from env import ABSPATH
import os
import json

from pyneuronjs import Neuron

dependency_tree = {}

dependency_file = os.path.normpath(
  os.path.join(ABSPATH, './test/fixtures/dependency.json')
)

try:
  dependency_json = open(dependency_file).read()
  dependency_tree = json.loads(dependency_json)
except Exception as e:
  print(e)

version = dependency_tree.get('_version')

# unset `dependency_file` which might leak the file structure of server
dependency_file = None

def resolve(module_ids):
  if type(module_ids) is not list:
    return _resolve(module_ids)

  module_ids = [
    _resolve(i).replace('/', '~')
    for i in module_ids
  ]

  return '/concat' + ','.join(module_ids)

def _resolve(module_id):
  return '/mod' + '/' + module_id.replace('@', '/')

neuron = Neuron(
  version=version,
  dependency_tree=dependency_tree,
  resolve=resolve,
  debug=False,
  js_config={
  }
)

neuron.facade('home/a.js', {
  'a': 1
})
# neuron.combo('home', 'b@0.1.0', 'c')

neuron.css('home/style.css')
neuron.css('b/style.css', 'c/style.css')

neuron.analyze()
neuron.analyze()
neuron.analyze()

# -> <link rel="" href="//s1.xhscdn.com/">
print(neuron.output())
print(neuron.output_css())
