#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""

import json

class neuron(object):
  # @param {dict} options
  # - 
  def __init__(self, **options):
    option_list = [
      ('dependency_tree', {}),
      ('decorate', neuron._default_decorator),
      ('path', '')
    ]
    for key, default in option_list:
      setattr(self, key, options.get(key) or default)

    if self.path.startswith('/'):
      self.path = self.path[1:]

    if self.path.endswith('/'):
      self.path = self.path[0:-1]

    self.facades = []
    self.combos = []
    self.walker = walker(self.dependency_tree)
    self.packages = []

  @staticmethod
  def _default_decorator(pathname):
    return pathname

  def facade(self, module_id, data):
    self.facades.append(
      (module_id, data or {})
    )
    return ''

  # defines which packages should be comboed
  def combo(self, *package_names):
    self.combos.append(package_names)
    return ''

  # TODO
  def css(self):
    return ''

  # TODO
  def output_css(self):
    return ''

  def output(self):
    self._analysis()

    return '\n'.join([
      self._output_neuron(),
      self._output_config(),
      self._output_scripts(),
      self._output_facades()
    ])

  def _output_facades(self):
    return '\n'.join([
      '<script>',
      '\n'.join([
        self._output_facade(package_name, data)
        for package_name, data in self.facades
      ]),
      '</script>'
    ])

  def _output_facade(self, package_name, data):
    return 'facade(\'%s\', %s)' % (package_name, json.dumps(data))

  def _output_loaded(self):
    pass

  def _output_neuron(self):
    return self.decorate(self.path + '/neuron.js')

  def _output_scripts(self):
    if not len(self.combos):
      return self._output_all_scripts()

    def dec(package_name):
      url = self._package_to_path(package_name, '*')
      return url

    already = []
    scripts = []
    package_names = [] + self.package_names
    for combo in self.combos:
      combo = self._clean_combo(combo, already, package_names)
      if len(combo):
        scripts.append(self.decorate(map(dec, combo)))

    # The ones not in combos
    for package_name in package_names:
      scripts.append(self.decorate(dec(package_name)))

    return '\n'.join(scripts)

  def _clean_combo(self, combo, already, package_names):
    combo = list(combo)

    def clean(item):
      if item in already:
        return False
      if item not in package_names:
        return False

      index = package_names.index(item)
      package_names.pop(index)
      already.append(item)
      return item

    combo = map(clean, combo)
    return filter(lambda x: x, combo)

  def _output_all_scripts(self):
    return '\n'.join([
      self.decorate(self._package_to_path(package_name, version))
      for package_name, version in self.packages
    ])

  def _package_to_path(self, package_name, version):
    return '/'.join([
      self.path,
      package_name,
      version,
      package_name + '.js'
    ])

  def _output_config(self):
    return ''

  def _analysis(self):
    self.walker.look_up(self.facades, self.packages)
    self.package_names = [
      package_name
      for package_name, version in self.packages
    ]


# {
#   "a": {
#   "*": {
#     "dependencies": {
#     "b": "*"
#     }
#   }
#   },
#   "b": {
#   "*": {}
#   }
# }
class walker(object):
  def __init__(self, tree):
    self.tree = tree

  # @param {list} entries
  # @param {list} host_list where the result will be appended to
  def look_up(self, entries, host_list):
    ordered = uniqueOrderedList()
    parsed_entries = []

    for entry, data in entries:
      self._walk_down(entry, ordered, parsed_entries)

    ordered.reverse()
    host_list += [
      (package_name, '*')
      for package_name in ordered
    ]

  # walk down 
  # @param {list} entry list of package names
  # @param {dict} tree the result tree to extend
  # @param {list} parsed the list to store parsed entries
  def _walk_down(self, entry, ordered, parsed):
    if entry in parsed:
      return
    parsed.append(entry)

    if entry not in self.tree:
      return

    # TODO: support real version
    dependencies = self._get_dependencies(entry)

    ordered.push(entry)
    ordered += dependencies

    index_entry = ordered.index(entry)
    for dep in dependencies:
      if dep not in ordered:
        ordered.push(dep)
      else:
        index_dep = ordered.index(dep)
        if index_dep <= index_entry:
          ordered.swap(index_entry, index_dep)
      
      self._walk_down(dep, ordered, parsed)

  def _get_dependencies(self, package_name):
    if package_name not in self.tree:
      return []

    return walker.access(
      self.tree,
      [package_name, '*', 'dependencies'],
      {}
    ).keys()

  @staticmethod
  def access(obj, keys, default):
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
      return super(self.__class__, self).__add__(other)

    for item in other:
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


__TEMPLATE = {
  'js'    : '<script%s src="%s"></script>',
  'css'   : '<link%s rel="stylesheet" href="%s">',
  'other' : '<img%s alt="" src="%s"/>'
}

def decorate(url, type_, extra=''):
  extra = ' ' + extra if extra else ''
  return __TEMPLATE.get(type_) % (extra, url)
