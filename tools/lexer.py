#!/usr/bin/env python3

"""Frontend to the Tartak lexer.

SYNOPSIS:
    python3 tools/lexer.py --help
    python3 tools/lexer.py <rules> <file> [<output>]


USAGE:
    The lexer frontend takes a <file> and tokenizes it according to rules described by
    <rules>.
    The result of the lexing process is a JSON encoded list of tokens.

    The lexing stops the moment an end-of-file is reached, i.e. input string is exhausted, or
    the lexer encounters a sequence it cannot recognize.
    In the latter situation lexer report the error and tells where to look for it giving its full
    location (line and character position).

    The output is by default written to a file called "a.tokens".
    This behaviour can be overriden by specifying the <output> operand.
    If it is a path, lexer will check if it can create the output file by writing empty string to it;
    in case of error during lexing the file is removed.
    If the file cannot be created - lexer aborts.
    If the <output> operand is a single hyphen character "-" the output is written to standard output.


BUGS:
    Any bugs should be reported on Tartak's github page.
    This tool operates on Tartak version {tartak_version}.
"""

import glob
import json
import os
import sys

sys.path.insert(1, os.getcwd())

try:
    from tartak import lexer
    from tartak import __version__ as VERSION
except ImportError as e:
    print('fatal: cannot import backend: {0}'.format(e))
    print('note:  check if Tartak is correctly installed on your system (if it is, check your Python path)')
    exit(127)


args = sys.argv[1:]

if len(args) < 2 or len(args) > 3:
    if args and args[0] != '--help':
        print('fatal: invalid number of operands: expected between 2 and 3 but got {0}'.format(len(args)))
        exit(1)

if args[0] == '--help':
    print(__help__.format(tartak_version=VERSION))
    exit(0)


LEXER_RULES = (args[0] if os.path.isfile(args[0]) else None)
PATH = (args[1] if os.path.isfile(args[0]) else None)
OUTPUT = (args[2] if len(args) == 3 else 'a.tokens')

if path is None:
    print('"{0}" does not point to a file'.format(args[0]))
    exit(2)

ifstream = open(path, 'r')
text = ifstream.read()
ifstream.close()


KEYWORDS = [
        'import',
        'using',

        'namespace',
        'class',
        'function',

        'int',
        'bool',
        'float',
        ]

GRAMMAR_CHARS = [
        ('lparen', '('),
        ('rparen', ')'),
        ('eos', ';'),
        ('stream-out', '<<'),
        ('stream-in', '>>'),
        ]


tknzr = source.tokenizer.Tokenizer()

for k in KEYWORDS:
    if not k: continue
    tknzr.addRule(name='keyword-{0}'.format(k), group='keyword', rule=k, type='string')

for name, rule in GRAMMAR_CHARS:
    tknzr.addRule(name=name, group='grammar_chars', rule=rule, type='string')

tknzr.addRule(name='name', rule='[a-zA-Z_][a-zA-Z0-9_]*', type='regex')
tknzr.addRule(name='comment-inline', rule='//.*(\n|$)', type='regex')
tknzr.addRule(name='comment-block', rule='(?s)/\*.*?\*/', type='regex')

tokens = []
tknzr.feed(text).tokenise()
raw = list(tknzr)
tokens = [i for i in raw if i[1][:7] != 'comment']
print('raw tokens: {0}'.format(len(raw)))
print('meaningful (without comments) tokens: {0} ({1}% less)'.format(len(tokens), round((len(raw)-len(tokens))/len(raw)*100, 2)))
#print(tokens)

PARSER_RULES = [
        ('import-statement', 'keyword-import name ";"'),
        ]

prsr = source.parser.Parser(tokens)
for name, pattern in PARSER_RULES: prsr.addRule(name, source.parser.deserialise(pattern))
#prsr.parse()
