#!/usr/bin/env python3

import json
import os
import re
import sys
import unittest

if '--no-path-guess' not in sys.argv:
    if os.path.split(os.getcwd())[1] == 'tartak': sys.path.insert(0, '.') # is current directory is named 'tartak', assume we are in development directory
    if os.path.split(os.getcwd())[1] == 'tests': sys.path.insert(0, '..') # is current directory is named 'tests', assume we are in testing directory

import tartak


# Helper functions
def getDefaultLexer(string):
    lxr = tartak.lexer.Lexer(string)
    (lxr.append(tartak.lexer.StringRule(pattern='if', name='if', group='keyword'))
        .append(tartak.lexer.StringRule(pattern='pass', name='pass', group='keyword'))
        .append(tartak.lexer.RegexRule(pattern='[a-zA-Z_][a-zA-Z0-9_]*', name='name', group='name'))
        .append(tartak.lexer.StringRule(pattern='==', name='eq', group='operator'))
        .append(tartak.lexer.StringRule(pattern='=', name='assign', group='operator'))
        .append(tartak.lexer.StringRule(pattern=':', name='colon', group='operator'))
        .append(tartak.lexer.RegexRule(pattern='(0|[1-9][0-9]*)', name='dec', group='int'))
        .append(tartak.lexer.RegexRule(pattern='0x[0-9a-fA-F]+', name='hex', group='int'))
        .append(tartak.lexer.RegexRule(pattern='0o[0-7]+', name='oct', group='int'))
        )
    return lxr


def readfile(path):
    with open(path, 'r') as ifstream: string = ifstream.read()
    return string


# Logic code
class LexerTests(unittest.TestCase):
    def testLexingSingleKeyword(self):
        string = 'if'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize().tokens()
        self.assertEqual('if', tokens[0].type())
        self.assertEqual('keyword', tokens[0].group())
        self.assertEqual('if', tokens[0].value())

    def testLexingTrickyIdentifier(self): # this test makes sure that Tartak doesn't tokenize 'ifstream' as 'if', 'stream'
        string = 'ifstream'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize().tokens()
        self.assertEqual('name', tokens[0].type())
        self.assertEqual('name', tokens[0].group())
        self.assertEqual('ifstream', tokens[0].value())

    def testRawTokensContainWhitespace(self):
        string = '  if'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize().tokens(raw=True)
        self.assertEqual('space', tokens[0].type())
        self.assertEqual('whitespace', tokens[0].group())
        self.assertEqual('  ', tokens[0].value())

    def testLexerIncludesIndentationInTokens(self):
        string = 'if 0:\n    pass'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(indent=True).tokens()
        self.assertEqual('if', tokens[0].type())
        self.assertEqual('keyword', tokens[0].group())
        self.assertEqual('if', tokens[0].value())
        self.assertEqual('dec', tokens[1].type())
        self.assertEqual('int', tokens[1].group())
        self.assertEqual('0', tokens[1].value())
        self.assertEqual('colon', tokens[2].type())
        self.assertEqual('operator', tokens[2].group())
        self.assertEqual(':', tokens[2].value())
        self.assertEqual('space', tokens[3].type())
        self.assertEqual('whitespace', tokens[3].group())
        self.assertEqual('    ', tokens[3].value())
        self.assertEqual('pass', tokens[4].type())
        self.assertEqual('keyword', tokens[4].group())
        self.assertEqual('pass', tokens[4].value())

    def testUnrecognizedSequencesThrowError(self):
        string = '$'
        lexer = getDefaultLexer(string)
        self.assertRaises(tartak.errors.LexerError, lexer.tokenize)

    def testUnrecognizedSequencesSaveError(self):
        string = '$$$'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('tartak', tokens[0].group())
        self.assertEqual('invalid', tokens[0].type())
        self.assertEqual('$$$', tokens[0].value())
        self.assertEqual(1, len(tokens)) # invalid chars should be grouped together

    def testUnrecognizedSequencesDropError(self):
        string = '$answer = 42'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='drop').tokens()
        self.assertEqual('name', tokens[0].group())
        self.assertEqual('name', tokens[0].type())
        self.assertEqual('answer', tokens[0].value())

    def testUnrecognizedSequencesConsumesOnlyInvalidSequenceAndNotFollowingWhitespace(self):
        string = 'answer$ = 42'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('tartak', tokens[1].group())
        self.assertEqual('invalid', tokens[1].type())
        self.assertEqual('$', tokens[1].value())

    def testLexingSinglequotedString(self):
        string = "s = 'string'"
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('single', tokens[2].type())
        self.assertEqual("'string'", tokens[2].value())

    def testLexingDoublequotedString(self):
        string = 's = "string"'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('double', tokens[2].type())
        self.assertEqual('"string"', tokens[2].value())

    def testLexingTripleSinglequotedString(self):
        string = """s = '''string
        '''"""
        lexer = getDefaultLexer(string).setFlag('string-sgl-triple')
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('triple', tokens[2].type())
        self.assertEqual("'''string\n        '''", tokens[2].value())

    def testLexingTripleDoublequotedString(self):
        string = '''s = """string
        """'''
        lexer = getDefaultLexer(string).setFlag('string-dbl-triple')
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('triple', tokens[2].type())
        self.assertEqual('"""string\n        """', tokens[2].value())


if __name__ == '__main__':
    unittest.main()
