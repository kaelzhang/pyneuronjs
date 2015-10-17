from env import ABSPATH
import os

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

print version, dependency_tree

nr = Neuron(
  version=version,
  dependency_tree=dependency_tree,
  # resolve=resolve,
  path='mod',
  debug=True
)

nr.facade('home')
nr.combo()

print nr.output()
