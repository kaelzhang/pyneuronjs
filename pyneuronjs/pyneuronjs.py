#

__author__ = 'Kael Zhang'

import json
import hashlib

from .walker import Walker
import tools
import module


class Neuron(object):
    '''
    '''

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

        self._analyzed = False

        # allow a facade with several different data
        self._facades = []

        # a single css file should not be loaded more than once
        self._csses = set([])
        self._loaded = set([])

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

    @tools.before_analysis
    def facade(self, module_id, data=None):
        self._facades.append(
            (module_id, data)
        )

        # Actually, neuron.facade() will output nothing
        return ''

    # defines which packages should be comboed
    @tools.before_analysis
    def combo(self, *package_names):
        # If debug, combos will not apply
        if not self._is_debug() and len(package_names) > 1:
            self._combos.append(package_names)
        return ''

    @tools.before_analysis
    def css(self, css_module):
        self._csses.add(css_module)
        return ''

    def output_css(self):
        self.analyze()
        return self._get_joiner().join([
            Neuron.decorate(
                self.resolve(module.normalize_id(id)),
                'css'
            )
            for id in self._csses
        ])

    @tools.memoize('_get_identifier_hash')
    def output(self):
        self.analyze()
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

    # prevent duplicated analysis
    @tools.before_analysis
    def analyze(self):
        self._analyzed = True

        facade_module_ids = [module_id for module_id, data in self._facades]

        # _packages:
        # {
        #   'a': set(['(1.1.0', ''), ('2.0.0', '')]),
        #   'b': set([('0.0.1', '')])
        # }

        # _graph:
        # neuron.config.graph for javascript
        self._packages, self._graph = self._walker.look_up(facade_module_ids)

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

        def select(name, version, path):
            cleaned.append((name, version, path))
            package_id = module.package_id(name, version)
            self._loaded.add(package_id)

        for item in combo:
            name, version, path = module.parse_module_id(item)

            # - prevent useless package
            # - removes already-comboed packages from self._packages
            #       to prevent duplication
            if name not in self._packages:
                continue
            version_paths = self._packages[name]

            # 'a' -> all versions of 'a'
            if version == '*':
                for v, p in version_paths:
                    select(name, v, p)
                self._packages.pop(name)

            # 'a@1.0.0' -> only a@1.0.0
            else:
                if (version, path) not in version_paths:
                    continue
                version_paths.remove((version, path))
                select(name, version, path)

                if not len(version_paths):
                    self._packages.pop(name)

        return cleaned

    def _output_neuron(self):
        return Neuron.decorate(self.resolve('neuron.js'), 'js')

    def _output_scripts(self):
        output = []
        self._decorate_combos_scripts(output)

        for name in self._packages:
            for version, path in self._packages[name]:
                self._loaded.add(module.package_id(name, version))
                self._decorate_script(output, (name, version, path))

        return ''.join(output)

    def _decorate_combos_scripts(self, output):
        for combo in self._combos:
            # should not combo a single file
            if len(combo) == 1:
                self._decorate_script(output, combo[0])
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

    def _decorate_script(self, output, module_tuple):
        script = Neuron.decorate(
            self.resolve(module.module_id(*module_tuple)),
            'js',
            'async'
        )
        output.append(script)

    USER_CONFIGS = ['path', 'resolve']

    def _output_config(self):
        config = {
            'loaded': self._json_dumps(list(self._loaded)),
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
            self._output_facade(module_id, data)
            for module_id, data in self._facades
        ])

    def _output_facade(self, module_id, data):
        json_str = ''
        if data:
            json_str = ', ' + self._json_dumps(data)
        return 'facade(\'%s\'%s);' % (module_id, json_str)

    def _json_dumps(self, obj):
        if self._is_debug():
            return json.dumps(obj, indent=2)
        return json.dumps(obj, separators=(',', ':'))

    # creates the hash according to the facades
    def _get_identifier_hash(self):
        s = 'pyneuron:' + self.version + ':' + ','.join([
            package_name for package_name, data in self._facades.sort()
        ])

        m = hashlib.sha1()
        m.update(s)
        return m.hexdigest()[0:8]

    ASSET_TEMPLATE = {
        'js': '<script%s src="%s"></script>',
        'css': '<link%s rel="stylesheet" href="%s">',
        'other': '<img%s alt="" src="%s"/>'
    }

    @staticmethod
    def decorate(url, type_, extra=''):
        extra = ' ' + extra if extra else ''
        return Neuron.ASSET_TEMPLATE.get(type_) % (extra, url)
