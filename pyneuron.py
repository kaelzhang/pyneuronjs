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
      ('path', ''),
      ('debug', False),
      ('version', 0),
      ('cache', None),
      ('config', {})
    ]
    for key, default in option_list:
      setattr(self, key, options.get(key) or default)

    if hasattr(self.debug, '__call__'):
      self._is_debug = self._is_debug_fn
    else:
      self.is_debug = bool(self.debug)
      self._is_debug = self._is_debug_bool

    # /mod  -> mod
    # mod/  -> mod
    # /mod/ -> mod 
    if self.path.startswith('/'):
      self.path = self.path[1:]
    if self.path.endswith('/'):
      self.path = self.path[0:-1]

    self._version = str(self.version)
    self._outputted = False
    self._facades = []

    # list.<tuple>
    self._combos = []
    self._walker = Walker(self.dependency_tree)
    self._packages = []

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
    self._analysis_combos()

    return '\n'.join([
      self._output_neuron(),
      self._output_scripts(),
      '<script>',
      self._output_config(),
      self._output_facades(),
      '</script>'
    ])

  def _output_neuron(self):
    return decorate(self.resolve(self.path + '/neuron.js'), 'js')

  def _output_config(self):
    return 

  # creates the hash according to the facades
  def _get_identifier_hash():
    s = self.version + ':' + ','.join([
      package_name for package_name, data in self._facades.sort()
    ])

    m = hashlib.sha1()
    m.update(s)
    return m.hexdigest()[0:8]

  def _output_facades(self):
    return '\n'.join([
      '<script>',
      '\n'.join([
        self._output_facade(package_name, data)
        for package_name, data in self._facades
      ]),
      '</script>'
    ])

  def _output_facade(self, package_name, data):
    json_str = ''
    if data:
      json_str = ', ' + json.dumps(data)
    return 'facade(\'%s\'%s)' % (package_name, json_str)

  def _output_loaded(self):
    pass

  def _output_scripts(self):
    if self._is_debug():
      return ''

    if not len(self._combos):
      return self._output_all_scripts()

    def resolve(package_name):
      url = self.resolve(self._package_to_path(package_name, '*'))
      return url

    return '\n'.join(scripts)

  def _output_all_scripts(self):
    return '\n'.join([
      decorate(
        self.resolve(
          self._package_to_path(package_name, version)
        ), 
        'js',
        'async'
      )
      for package_name, version in self.packages
    ])

  def _package_to_path(self, package_name, version):
    return '/'.join([
      self.path,
      package_name,
      version,
      package_name + '.js'
    ])

  def _analysis(self):
    self._walker.look_up(self._facades, self._packages)
    self._package_names = [
      package_name
      for package_name, version in self._packages
    ]

  def _analysis_combos(self):
    # combos
    remains = [] + self._package_names
    for combo in self._combos:
      combo = self._clean_combo(combo, already, remains)
      if len(combo):
        scripts.append(
          decorate(
            self.resolve(map(dec, combo)),
            'js'
            'async'
          )
        )

    # The ones not in combos
    for package_name in remains:
      scripts.append(decorate(resolve(package_name), 'js', 'async'))

  def _clean_combo(self, combo, already, remains):
    combo = list(combo)

    def clean(item):
      # prevent useless package
      # and prevent duplication
      if item not in remains:
        return False

      index = remains.index(item)
      remains.pop(index)
      return item

    combo = map(clean, combo)
    return filter(lambda x: x, combo)


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
  def look_up(self, entries):
    ordered = uniqueOrderedList()

    parsed_entries = []
    for entry, data in entries:
      self._walk_down(entry, '*', ordered, parsed_entries)
    ordered.reverse()

    return list(ordered)

  # def _get_package(name, version):
  #   return Walker.access(this._tree, [name, version], {})

  # walk down 
  # @param {list} entry list of package names
  # @param {dict} tree the result tree to extend
  # @param {list} parsed the list to store parsed entries
  def _walk_down(self, name, version, ordered, parsed):
    package_id = format(name + '@' + version)

    if package_id in parsed:
      return
    parsed.append(package_id)

    package = self._get_package(name, version)
    if not package:
      return
    ordered.push(package_id)

    dependencies = package['dependencies']
    if not dependencies:
      return

    index_entry = ordered.index(package_id)
    for dep_name in dependencies:
      dep_version = dependencies[dep_name]
      dep_id = format(dep_name, dep_version)
      if dep_id not in ordered:
        ordered.push(dep_id)
      else:
        index_dep = ordered.index(dep_id)
        if index_dep <= index_entry:
          ordered.swap(index_entry, index_dep)
      
      self._walk_down(dep_name, dep_version, ordered, parsed)

  def _get_package(self, name, version):
    return access(self._tree, [name, version])


def format(name, version):
  return name + '@' + version

# Try to deeply access a dict
def access(obj, keys, default=None):
  ret = obj
  for key in keys:
    if type(ret) is not dict or key not in ret:
      return default
    ret = ret[key]
  return ret


# We need an ordered unique list
# which should be able to swap items,
# so we have to implement by ourself
class uniqueOrderedList(list):
  def __iadd__(self, other):
    if type(other) is not list and type(other) is not self.__class__:
      # Actually, it will fail
      return super(self.__class__, self).__add__(other)

    for item in other:
      # In python, `+=` will change the referenced list object,
      # even if passed as a parameter to a function, 
      # unlike javascript and many other languages.
      # So, we need to change the original list
      self.push(item)
    return self

  def __add__(self, other):
    new = uniqueList()
    new += self
    new += other
    return new

  # push unique
  def push(self, item):
    if item not in self:
      self.append(item)

  def swap(self, index_a, index_b):
    self[index_a], self[index_b] = self[index_b], self[index_a]


_TEMPLATE = {
  'js'    : '<script%s src="%s"></script>',
  'css'   : '<link%s rel="stylesheet" href="%s">',
  'other' : '<img%s alt="" src="%s"/>'
}

def decorate(url, type_, extra=''):
  extra = ' ' + extra if extra else ''
  return _TEMPLATE.get(type_) % (extra, url)
