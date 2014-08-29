#!/usr/bin/python3

"""Frontend to Tartak parser.
"""

import json
import os
import sys

sys.path.insert(1, os.getcwd())

try:
    import tartak
except ImportError as e:
    print('fatal: cannot import backend: {0}'.format(e))
    print('note:  check if Tartak is correctly installed on your system (if it is, check your Python path)')
    exit(127)

args = sys.argv[1:]

if not args and not os.path.isfile('a.tokens'):
    print('fatal: parser does not know what file to load - no path given and file "a.tokens" not found in current directory')
    exit(1)

if args and args[0] in ['-h', '--help']:
    print(__doc__)
    exit(0)


if not args and os.path.isfile('a.tokens'):
    INPUT = 'a.tokens'
elif args:
    INPUT = args[0]

if not os.path.isfile(INPUT):
    print('fatal: there is not such file: "{0}"'.format(INPUT))
    exit(2)

ifstream = open(INPUT, 'r')
string = ifstream.read()
ifstream.close()

lexer = tartak.lexer.Lexer().loads(json.loads(string))
print('loaded lexer state\n------------------')
print(''.join([i.value() for i in lexer.tokens(raw=True)]))

parser = tartak.parser.NewParser(lexer)
parser.append(name='element', pattern=[{'type': 'string', 'value': ['['], 'mod': ''}])
