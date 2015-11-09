#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""

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

        joiner = self._get_joiner()

        if self._is_debug():
            return joiner.join([
                self._output_neuron(),
                '<script>',
                self._output_facades(),
                '</script>'
            ])

        return joiner.join([
            self._output_neuron(),
            self._output_scripts(),
            '<script>',
            self._output_config(),
            self._output_facades(),
            '</script>'
        ])

    def _get_joiner(self):
        joiner = ''
        if self._is_debug():
            joiner = '\n'
        return joiner

    def _analysis(self):
        # {
        #   'a': set(['1.1.0', '2.0.0']),
        #   'b': set(['0.0.1'])
        # }
        (self._packages, self._graph) = self._walker.look_up(self._facades)

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
        cleaned = []

        def select(name, version):
            cleaned.append((name, version))
            package_id = Neuron.package_id(name, version)
            self._loaded.append(package_id)

        for item in combo:
            (name, version) = Neuron.parse_package_id(item)

            # prevent useless package
            # and prevent duplication
            if name not in self._packages:
                continue
            versions = self._packages[name]

            # 'a' -> all versions of 'a'
            if version == '*':
                for v in versions:
                    select(name, v)
                self._packages.pop(name)
            # 'a@1.0.0' -> only a@1.0.0
            else:
                if version not in versions:
                    continue
                versions.remove(version)
                select(name, version)

                if not len(versions):
                    self._packages.pop(name)

        return cleaned

    def _output_neuron(self):
        return decorate(self.resolve('neuron.js'), 'js')

    def _output_scripts(self):
        output = []
        self._decorate_combos_scripts(output)

        for name in self._packages:
            for version in self._packages[name]:
                self._loaded.append(Neuron.package_id(name, version))
                self._decorate_script(output, name, version)

        return ''.join(output)

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
            'loaded': self._json_dumps(self._loaded),
            'graph': self._json_dumps(self._graph)
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

    def _json_dumps(self, obj):
        if self._is_debug():
            return json.dumps(obj, indent=2)
        return json.dumps(obj, separators=(',', ':'))

    def _output_facade(self, package_name, data):
        json_str = ''
        if data:
            json_str = ', ' + self._json_dumps(data)
        return 'facade(\'%s\'%s);' % (package_name, json_str)

    # creates the hash according to the facades
    def _get_identifier_hash():
        s = 'pyneuron:' + self.version + ':' + ','.join([
            package_name for package_name, data in self._facades.sort()
        ])

        m = hashlib.sha1()
        m.update(s)
        return m.hexdigest()[0:8]

    @staticmethod
    def parse_package_id(package_id):
        splitted = package_id.split('@')
        if len(splitted) == 1:
            return (package_id, '*')

        return (splitted[0], splitted[1])


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
        self.guid = 0

    # @param {list} entries
    # @param {list} host_list where the result will be appended to
    def look_up(self, facades):
        self.parsed = []
        self.selected = {}
        self.map = {}

        facade_node = {}
        self.graph = {
            '_': facade_node
        }
        for package_id, data in facades:
            (name, version) = Neuron.parse_package_id(package_id)
            self._walk_down(name, version, version, facade_node)

        return (self.selected, self.graph)

    def _guid(self):
        uid = self.guid
        self.guid += 1
        return uid

    # walk down
    # @param {list} entry list of package names
    # @param {dict} tree the result tree to extend
    # @param {list} parsed the list to store parsed entries
    def _walk_down(self, name, range_, version, dependency_node):
        # if the node is already parsed,
        # sometimes we still need to add the dependency to the parent node
        package_range_id = Neuron.package_id(name, range_)
        package_id = Neuron.package_id(name, version)
        (node, index) = self._get_graph_node(package_id, version)
        dependency_node[package_range_id] = index

        if package_id in self.parsed:
            return
        self.parsed.append(package_id)

        self._select(name, version)

        # Walk dependencies
        dependencies = self._get_dependencies(name, version)
        if not dependencies:
            return

        current_dependency_node = self._get_dependency_node(node)
        for dep in dependencies:
            (dep_name, dep_range) = Neuron.parse_package_id(dep)
            dep_version = dependencies[dep]
            self._walk_down(dep_name, dep_range, dep_version,
                            current_dependency_node)

    def _get_dependencies(self, name, version):
        return Walker.access(self._tree, [name, version, 'dependencies'])

    def _select(self, name, version):
        selected = self.selected
        if name not in selected:
            selected[name] = set()

        selected[name].add(version)

    def _get_graph_node(self, package_id, version):
        if package_id in self.map:
            index = self.map[package_id]
            return (self.graph[index], index)

        index = self._guid()
        self.map[package_id] = index
        node = [version]
        self.graph[index] = node
        return (node, index)

    def _get_dependency_node(self, node):
        if len(node) == 1:
            dependency_node = {}
            node.append(dependency_node)
            return dependency_node
        return node[1]

    # Try to deeply access a dict
    @staticmethod
    def access(obj, keys, default=None):
        ret = obj
        for key in keys:
            if type(ret) is not dict or key not in ret:
                return default
            ret = ret[key]
        return ret


_TEMPLATE = {
    'js': '<script%s src="%s"></script>',
    'css': '<link%s rel="stylesheet" href="%s">',
    'other': '<img%s alt="" src="%s"/>'
}


def decorate(url, type_, extra=''):
    extra = ' ' + extra if extra else ''
    return _TEMPLATE.get(type_) % (extra, url)
