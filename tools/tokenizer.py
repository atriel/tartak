#!/usr/bin/env python3

"""This is a frontend to the Mar tokenizer.
"""

import json
import os
import sys

from mar import source


args = sys.argv[1:]

if len(args) < 1:
    print('fatal: requires a file')
    exit(1)

path = (args[0] if os.path.isfile(args[0]) else None)

if path is None: raise TypeError('"{0}" does not point to a file'.format(args[0]))


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
