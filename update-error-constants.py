#!/usr/bin/env python

import sys, os, os.path, re, codecs

BUILD_SOURCE_FILE = os.path.join("src", "lxml", "xmlerror.pxi")
BUILD_DEF_FILE    = os.path.join("src", "lxml", "includes", "xmlerror.pxd")

if len(sys.argv) < 2 or sys.argv[1].lower() in ('-h', '--help'):
    print("This script generates the constants in file %s" % BUILD_SOURCE_FILE)
    print("Call as")
    print(sys.argv[0], "/path/to/libxml2-doc-dir")
    sys.exit(len(sys.argv) > 1)

HTML_DIR = os.path.join(sys.argv[1], 'html')
os.stat(HTML_DIR) # raise an error if we can't find it

sys.path.insert(0, 'src')
from lxml import etree

# map enum name to Python variable name and alignment for constant name
ENUM_MAP = {
    'xmlErrorLevel'       : ('__ERROR_LEVELS',  'XML_ERR_'),
    'xmlErrorDomain'      : ('__ERROR_DOMAINS', 'XML_FROM_'),
    'xmlParserErrors'     : ('__PARSER_ERROR_TYPES',   'XML_'),
#    'xmlXPathError'       : ('__XPATH_ERROR_TYPES',   ''),
#    'xmlSchemaValidError' : ('__XMLSCHEMA_ERROR_TYPES',   'XML_'),
    'xmlRelaxNGValidErr'  : ('__RELAXNG_ERROR_TYPES',   'XML_'),
    }

ENUM_ORDER = (
    'xmlErrorLevel',
    'xmlErrorDomain',
    'xmlParserErrors',
#    'xmlXPathError',
#    'xmlSchemaValidError',
    'xmlRelaxNGValidErr')

COMMENT = """
# This section is generated by the script '%s'.

""" % os.path.basename(sys.argv[0])

def split(lines):
    lines = iter(lines)
    pre = []
    for line in lines:
        pre.append(line)
        if line.startswith('#') and "BEGIN: GENERATED CONSTANTS" in line:
            break
    pre.append('')
    for line in lines:
        if line.startswith('#') and "END: GENERATED CONSTANTS" in line:
            break
    post = ['', line]
    post.extend(lines)
    post.append('')
    return pre, post

def regenerate_file(filename, result):
    # read .pxi source file
    f = codecs.open(filename, 'r', encoding="utf-8")
    pre, post = split(f)
    f.close()

    # write .pxi source file
    f = codecs.open(filename, 'w', encoding="utf-8")
    f.write(''.join(pre))
    f.write(COMMENT)
    f.write('\n'.join(result))
    f.write(''.join(post))
    f.close()

collect_text = etree.XPath("string()")
find_enums = etree.XPath(
    "//html:pre[@class = 'programlisting' and contains(text(), 'Enum')]",
    namespaces = {'html' : 'http://www.w3.org/1999/xhtml'})

def parse_enums(html_dir, html_filename, enum_dict):
    PARSE_ENUM_NAME  = re.compile(r'\s*enum\s+(\w+)\s*{', re.I).match
    PARSE_ENUM_VALUE = re.compile(r'\s*=\s+([0-9]+)\s*(?::\s*(.*))?').match
    tree = etree.parse(os.path.join(html_dir, html_filename))
    enums = find_enums(tree)
    for enum in enums:
        enum_name = PARSE_ENUM_NAME(collect_text(enum))
        if not enum_name:
            continue
        enum_name = enum_name.group(1)
        if enum_name not in ENUM_MAP:
            continue
        print("Found enum", enum_name)
        entries = []
        for child in enum:
            name = child.text
            match = PARSE_ENUM_VALUE(child.tail)
            if not match:
                print("Ignoring enum %s (failed to parse field '%s')" % (
                        enum_name, name))
                break
            value, descr = match.groups()
            entries.append((name, int(value), descr))
        else:
            enum_dict[enum_name] = entries
    return enum_dict

enum_dict = {}
parse_enums(HTML_DIR, 'libxml-xmlerror.html',   enum_dict)
#parse_enums(HTML_DIR, 'libxml-xpath.html',      enum_dict)
#parse_enums(HTML_DIR, 'libxml-xmlschemas.html', enum_dict)
parse_enums(HTML_DIR, 'libxml-relaxng.html',    enum_dict)

# regenerate source files
pxi_result = []
append_pxi = pxi_result.append
pxd_result = []
append_pxd = pxd_result.append

append_pxd('cdef extern from "libxml/xmlerror.h":')
append_pxi('''\
# Constants are stored in tuples of strings, for which Cython generates very
# efficient setup code.  To parse them, iterate over the tuples and parse each
# line in each string independently.  Tuples of strings (instead of a plain
# string) are required as some C-compilers of a certain well-known OS vendor
# cannot handle strings that are a few thousand bytes in length.
''')

ctypedef_indent = ' '*4
constant_indent = ctypedef_indent*2

for enum_name in ENUM_ORDER:
    constants = enum_dict[enum_name]
    pxi_name, prefix = ENUM_MAP[enum_name]

    append_pxd(ctypedef_indent + 'ctypedef enum %s:' % enum_name)
    append_pxi('cdef object %s = (u"""\\' % pxi_name)

    prefix_len = len(prefix)
    length = 2 # each string ends with '\n\0'
    for name, val, descr in constants:
        if descr and descr != str(val):
            line = '%-50s = %7d # %s' % (name, val, descr)
        else:
            line = '%-50s = %7d' % (name, val)
        append_pxd(constant_indent + line)

        if name[:prefix_len] == prefix and len(name) > prefix_len:
            name = name[prefix_len:]
        line = '%s=%d' % (name, val)
        if length + len(line) >= 2040: # max string length in MSVC is 2048
            append_pxi('""",')
            append_pxi('u"""\\')
            length = 2 # each string ends with '\n\0'
        append_pxi(line)
        length += len(line) + 2 # + '\n\0'

    append_pxd('')
    append_pxi('""",)')
    append_pxi('')

# write source files
print("Updating file %s" % BUILD_SOURCE_FILE)
regenerate_file(BUILD_SOURCE_FILE, pxi_result)

print("Updating file %s" % BUILD_DEF_FILE)
regenerate_file(BUILD_DEF_FILE,    pxd_result)

print("Done")
