#

__author__ = 'Kael Zhang'

import json
import hashlib

from .walker import Walker
import tools
import module

ASSET_TEMPLATE = {
    'js': '<script%s src="%s"></script>',
    'css': '<link%s rel="stylesheet" href="%s">',
    'other': '<img%s alt="" src="%s"/>'
}


class Neuron(object):
    """
    """

    def __init__(self,
                 dependency_tree = {},
                 resolve         = None,
                 debug           = False,
                 version         = 0,
                 cache           = None,
                 js_config       = {}):

        if not resolve:
            resolve = Neuron._default_resolver

        self.dependency_tree     = dependency_tree
        self.resolve             = resolve
        self.debug               = debug
        self.version             = str(version)

        # TODO
        self.cache               = cache
        self.js_config           = js_config

        if hasattr(self.debug, b'__call__'):
            self._is_debug = self._is_debug_fn
        else:
            self.is_debug = bool(self.debug)
            self._is_debug = self._is_debug_bool

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

    @tools.beforeoutput
    def facade(self, module_id, data=None):
        self._facades.append(
            (module_id, data)
        )

        # Actually, neuron.facade() will output nothing
        return ''

    # defines which packages should be comboed
    @tools.beforeoutput
    def combo(self, *package_names):
        # If debug, combos will not apply
        if not self._is_debug() and len(package_names) > 1:
            self._combos.append(package_names)
        return ''

    # TODO
    @tools.beforecssoutput
    def css(self):
        return ''

    # TODO
    def output_css(self):
        return ''

    @tools.memoize('_get_identifier_hash')
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

        # _packages:
        # {
        #   'a': set(['1.1.0', '2.0.0']),
        #   'b': set(['0.0.1'])
        # }

        # _graph:
        # neuron.config.graph for javascript
        self._packages, self._graph = self._walker.look_up(self._facades)

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
            package_id = module.package_id(name, version)
            self._loaded.append(package_id)

        for item in combo:
            name, version, path = module.parse_module_id(item)

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
        return Neuron.decorate(self.resolve('neuron.js'), 'js')

    def _output_scripts(self):
        output = []
        self._decorate_combos_scripts(output)

        for name in self._packages:
            for version in self._packages[name]:
                self._loaded.append(module.package_id(name, version))
                self._decorate_script(output, name, version)

        return ''.join(output)

    def _decorate_combos_scripts(self, output):
        for combo in self._combos:
            # should not combo a single file
            if len(combo) == 1:
                name, version = combo[0]
                self._decorate_script(output, name, version)
                continue

            joined_combo = [
                module.module_id(*package)
                for package in combo
            ]

            script = Neuron.decorate(
                self.resolve(joined_combo),
                'js',
                'async'
            )
            output.append(script)

    def _decorate_script(self, output, name, version):
        script = Neuron.decorate(
            self.resolve(module.module_id(name, version)),
            'js',
            'async'
        )
        output.append(script)

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
    def _get_identifier_hash(self):
        s = 'pyneuron:' + self.version + ':' + ','.join([
            package_name for package_name, data in self._facades.sort()
        ])

        m = hashlib.sha1()
        m.update(s)
        return m.hexdigest()[0:8]

    @staticmethod
    def decorate(url, type_, extra=''):
        extra = ' ' + extra if extra else ''
        return ASSET_TEMPLATE.get(type_) % (extra, url)
