# Walker to walk the dependency tree

import module


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

        # `self.selected` has the structure like:
        # {
        #     '<name>': set([
        #         ('<version>', '<path>')
        #     ])
        # }
        self.selected = {}
        self.map = {}

        facade_node = {}
        self.graph = {
            '_': facade_node
        }
        for package_id, data in facades:
            name, version, path = module.parse_module_id(package_id)

            # If the module id facaded contains path, the path will be ignored
            self._walk_down(name, version, version, path, facade_node)

        return (self.selected, self.graph)

    def _guid(self):
        uid = self.guid
        self.guid += 1
        return uid

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
            dep_version = dependencies[dep]
            self._walk_down_non_facade(dep_name, dep_range, dep_version,
                            current_dependency_node)

    def _get_dependencies(self, name, version):
        return Walker.access(self._tree, [name, version, 'dependencies'])

    def _select(self, name, version, path = ''):
        selected = self.selected
        if name not in selected:
            selected[name] = set()

        selected[name].add((version, path))


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
