# Utility tools to parse a module

# format to module id
def module_id(name, version, path=''):
    # 'a', '*', '' -> 'a@*/a.js'
    # 'a', '*', '/' -> 'a@*/a.js'
    if not path or path == '/':
        path = '/' + name + '.js'

    return package_id(name, version) + path


def package_id(name, version):
    return name + '@' + version


def parse_package_id(id):
    splitted = id.split('@')
    if len(splitted) == 1:
        return (package_id, '*')

    return (splitted[0], splitted[1])
