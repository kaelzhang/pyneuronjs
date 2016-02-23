# Utility tools to parse a module


import re


# format to module id
# 'jquery' -> 'jquery@*/jquery.js'
def module_id(name, version, path=''):
    # 'a', '*', '' -> 'a@*/a.js'
    # 'a', '*', '/' -> 'a@*/a.js'
    if not path or path == '/':
        path = '/' + name + '.js'

    return package_id(name, version) + path


def normalize_id(id):
    return module_id(*parse_module_id(id))


def package_id(name, version):
    return name + '@' + version


REGEX_MODULE_ID = re.compile(
    r"""^
        ([^\/]+?)       # name
        (?:
            @
            ([^\/]+)    # version
        )?
        (\/.*)?         # path
        $""",
    re.X)

def parse_module_id(id):
    # there will always a match
    m = re.match(REGEX_MODULE_ID, id)

    if not m:
        raise ValueError('Invalid module id: "' + id + '", format: <name>[@<version>][/<path>]')

    path = m.group(3) or ''

    if path == '/':
        path = ''

    return (
        m.group(1),
        # version default to '*'
        m.group(2) or '*',
        path)

# returns the max satisfied version of the range
# @param {str} r Range
# @param {list} versions The list of existing versions
def max_satisfying(r, versions):
    # returns the range directly temporarily for now
    return r
