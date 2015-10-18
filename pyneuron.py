#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""

__all__ = ['Neuron', 'decorate', 'uniqueOrderedList']

import json
import hashlib

# Memoize 
def memoize(fn):
  def method(self, *args):
    # prevent saving cache for empty facades
    if not self.cache or not len(self.facades):
      return fn(self, *args)

    hash_id = self._get_identifier_hash()
    if self.cache.has(hash_id):
      return self.cache.get(hash_id)

    result = fn(self, *args)
    self.cache.save(hash_id, result)
    return result

  return method

def beforeoutput(fn):
  def method(self, *args):
    if self._outputted:
      return ''
    return fn(self, *args)

  return method

def beforecssoutput(fn):
  return fn


class Neuron(object):
  def __init__(self, **options):
    option_list = [
      ('dependency_tree', {}),
      ('resolve', Neuron._default_resolver),
      ('debug', False),
      ('version', 0),
      ('cache', None),
      ('js_config', {})
    ]
    for key, default in option_list:
      setattr(self, key, options.get(key) or default)

    if hasattr(self.debug, '__call__'):
      self._is_debug = self._is_debug_fn
    else:
      self.is_debug = bool(self.debug)
      self._is_debug = self._is_debug_bool

    self._version = str(self.version)
    self._outputted = False
    self._facades = []
    self._loaded = []

    # list.<tuple>
    self._combos = []
    self._walker = Walker(self.dependency_tree)

  def _is_debug_fn(self):
    return self.debug()

  def _is_debug_bool(self):
    return self.debug

  @staticmethod
  def _default_resolver(pathname):
    return '/' + pathname

  @beforeoutput
  def facade(self, module_id, data=None):
    self._facades.append(
      (module_id, data)
    )

    # Actually, neuron.facade() will output nothing
    return ''

  # defines which packages should be comboed
  @beforeoutput
  def combo(self, *package_names):
    # If debug, combos will not apply
    if not self._is_debug() and len(package_names) > 1:
      self._combos.append(package_names)
    return ''

  # TODO
  @beforecssoutput
  def css(self):
    return ''

  # TODO
  def output_css(self):
    return ''

  @memoize
  def output(self):
    self._outputted = True
    self._analysis()

    return '\n'.join([
      self._output_neuron(),
      self._output_scripts(),
      '<script>',
      self._output_config(),
      self._output_facades(),
      '</script>'
    ])

  def _analysis(self):
    # {
    #   'a': set(['1.1.0', '2.0.0']),
    #   'b': set(['0.0.1'])
    # }
    self._packages = self._walker.look_up(self._facades)

    combos = self._combos
    if not len(combos):
      return

    self._combos = []
    # self._combos
    # -> [('a', 'b'), ('b', 'c', 'd')]
    for combo in combos:
      combo = self._clean_combo(combo)
      if len(combo):
        self._combos.append(combo)

  def _clean_combo(self, combo):
    combo = list(combo)

    def clean(item):
      (name, version) = parse_package_id(item)
      package_id = Neuron.package_id(name, version)

      if package_id in self._loaded:
        return False
      self._loaded.append(package_id)

      # prevent useless package
      # and prevent duplication
      if name not in self._packages:
        return False

      if version not in self._packages[name]:
        return False

      self._packages[name].remove(version)
      if not len(self._packages[name]):
        self._packages.pop(name)

      return (name, version)

    combo = map(clean, combo)
    return filter(lambda x: x, combo)

  def _output_neuron(self):
    return decorate(self.resolve('neuron.js'), 'js')

  def _output_scripts(self):
    output = []
    self._decorate_combos_scripts(output)

    for name in self._packages:
      for version in self._packages[name]:
        self._loaded.append(Neuron.package_id(name, version))
        self._decorate_script(output, name, version)

    return '\n'.join(output)

  def _decorate_combos_scripts(self, output):
    for combo in self._combos:
      joined_combo = [
        Neuron.module_id(*package)
        for package in combo
      ]

      script = decorate(
        self.resolve(joined_combo),
        'js',
        'async'
      )
      output.append(script)

  def _decorate_script(self, output, name, version):
    script = decorate(
      self.resolve(Neuron.module_id(name, version)),
      'js',
      'async'
    )
    output.append(script)

  # format to module id
  @staticmethod
  def module_id(name, version, path=''):
    # 'a', '*', '' -> 'a@*/a.js'
    # 'a', '*', '/' -> 'a@*/a.js'
    if not path or path == '/':
      path = '/' + name + '.js'

    return Neuron.package_id(name, version) + path

  @staticmethod
  def package_id(name, version):
    return name + '@' + version

  USER_CONFIGS = ['path', 'resolve']

  def _output_config(self):
    config = {
      'loaded': json.dumps(self._loaded)
    }

    for key in Neuron.USER_CONFIGS:
      c = self.js_config.get(key)
      if c:
        config[key] = c

    config_pair = [
      key + ':' + config[key]
      for key in config
    ]

    return 'neuron.config({' + ','.join(config_pair) + '});'

  def _output_facades(self):
    return '\n'.join([
      self._output_facade(package_name, data)
      for package_name, data in self._facades
    ])

  def _output_facade(self, package_name, data):
    json_str = ''
    if data:
      json_str = ', ' + json.dumps(data)
    return 'facade(\'%s\'%s);' % (package_name, json_str)

  # creates the hash according to the facades
  def _get_identifier_hash():
    s = 'pyneuron:' + self.version + ':' + ','.join([
      package_name for package_name, data in self._facades.sort()
    ])

    m = hashlib.sha1()
    m.update(s)
    return m.hexdigest()[0:8]


class Walker(object):

  # @param {dict} tree
  # {
  #   "a": {
  #     "*": {
  #       "dependencies": {
  #         "b": "*"
  #       }
  #     }
  #   },
  #   "b": {
  #     "*": {}
  #   }
  # }
  def __init__(self, tree):
    self._tree = tree

  # @param {list} entries
  # @param {list} host_list where the result will be appended to
  def look_up(self, facades):
    parsed = []
    selected = {}

    for name, data in facades:
      self._walk_down(name, '*', selected, parsed)

    return selected

  # def _get_package(name, version):
  #   return Walker.access(this._tree, [name, version], {})

  # walk down 
  # @param {list} entry list of package names
  # @param {dict} tree the result tree to extend
  # @param {list} parsed the list to store parsed entries
  def _walk_down(self, name, version, selected, parsed):
    package_id = Neuron.package_id(name, version)

    if package_id in parsed:
      return
    parsed.append(package_id)

    select(selected, name, version)

    dependencies = self._get_dependencies(name, version)
    if not dependencies:
      return

    for dep_name in dependencies:
      self._walk_down(dep_name, dependencies[dep_name], selected, parsed)

  def _get_dependencies(self, name, version):
    return access(self._tree, [name, version, 'dependencies'])


def parse_package_id(package_id):
    splitted = package_id.split('@')
    if len(splitted) == 1:
      return (package_id, '*')

    return (splitted[0], splitted[1])

def select(dic, name, version):
  if name not in dic:
    dic[name] = set()

  dic[name].add(version)


# Try to deeply access a dict
def access(obj, keys, default=None):
  ret = obj
  for key in keys:
    if type(ret) is not dict or key not in ret:
      return default
    ret = ret[key]
  return ret


_TEMPLATE = {
  'js'    : '<script%s src="%s"></script>',
  'css'   : '<link%s rel="stylesheet" href="%s">',
  'other' : '<img%s alt="" src="%s"/>'
}

def decorate(url, type_, extra=''):
  extra = ' ' + extra if extra else ''
  return _TEMPLATE.get(type_) % (extra, url)
