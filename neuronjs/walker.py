# Walker to walk the dependency tree


from . import module

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
        facade_node = {}

        # `self.selected` has the structure like:
        # {
        #     '<name>': set([
        #         ('<version>', '<path>')
        #     ])
        # }
        self.selected = {}

        # see [here](https://github.com/kaelzhang/neuron/blob/master/doc/graph.md)
        self.graph = {
            '_': facade_node
        }

        # map to store the index of the dependency node
        self.index_map = {}
        
        for module_id in facades:
            name, range_, path = module.parse_module_id(module_id)

            # If the module id facaded contains path, the path will be ignored
            self._walk_down_facade(name, range_, path, facade_node)

        return (self.selected, self.graph)

    def _resolve_range(self, name, range_):
        if name not in self._tree:
            return

        versions = self._tree[name]
        return module.max_satisfying(range_, versions.keys())

    def _guid(self):
        uid = self.guid
        self.guid += 1
        return uid

    def _walk_down_facade(self, name, range_, path, dependency_node):
        # The offline ci could not know which facades to load,
        # so the range version of the facade is still not resolved. 
        version = self._resolve_range(name, range_) or range_
        self._walk_down(name, range_, version, path, dependency_node)

    def _walk_down_non_facade(self, name, range_, version, dependency_node):
        # If not facade, module should not contain `path`
        self._walk_down(name, range_, version, '', dependency_node)

    # walk down
    # @param {list} entry list of package names
    # @param {dict} tree the result tree to extend
    # @param {list} parsed the list to store parsed entries
    def _walk_down(self, name, range_, version, path, dependency_node):
        # if the node is already parsed,
        # sometimes we still need to add the dependency to the parent node
        package_range_id = module.package_id(name, range_)
        package_id = module.package_id(name, version)
        node, index = self._get_graph_node(package_id, version)
        dependency_node[package_range_id] = index

        if package_id in self.parsed:
            # prevent parsing duplicately.
            return

        self.parsed.append(package_id)

        self._select(name, version, path)

        # Walk dependencies
        dependencies = self._get_dependencies(name, version)
        if not dependencies:
            return

        current_dependency_node = self._get_dependency_node(node)
        for dep in dependencies:
            dep_name, dep_range, dep_path = module.parse_module_id(dep)

            # The dependency version of a package is already resolved by 
            #   neuron-package-dependency
            dep_version = dependencies[dep]
            self._walk_down_non_facade(
                dep_name,
                dep_range,
                dep_version,
                current_dependency_node)

    def _get_dependencies(self, name, version):
        return Walker.access(self._tree, [name, version, 'dependencies'])

    def _select(self, name, version, path = ''):
        selected = self.selected
        if name not in selected:
            selected[name] = set()

        selected[name].add((version, path))

    def _get_graph_node(self, package_id, version):
        if package_id in self.index_map:
            index = self.index_map[package_id]
            return (self.graph[index], index)

        index = self._guid()
        self.index_map[package_id] = index
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
