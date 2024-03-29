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


DEBUG = False


# Helper functions
def getDefaultLexer(string='', triple_strings=False):
    lxr = tartak.lexer.Lexer(string=string)
    (lxr.append(tartak.lexer.StringRule(pattern='if', name='if', group='keyword'))
        .append(tartak.lexer.StringRule(pattern='pass', name='pass', group='keyword'))
        .append(tartak.lexer.RegexRule(pattern='[a-zA-Z_][a-zA-Z0-9_]*', name='name', group='name'))
        .append(tartak.lexer.StringRule(pattern='==', name='eq', group='operator'))
        .append(tartak.lexer.StringRule(pattern='=', name='assign', group='operator'))
        .append(tartak.lexer.StringRule(pattern=':', name='colon', group='operator'))
        .append(tartak.lexer.StringRule(pattern=';', name='semicolon', group='operator'))
        .append(tartak.lexer.RegexRule(pattern='(0|[1-9][0-9]*)', name='dec', group='integer'))
        .append(tartak.lexer.RegexRule(pattern='0x[0-9a-fA-F]+', name='hex', group='integer'))
        .append(tartak.lexer.RegexRule(pattern='0o[0-7]+', name='oct', group='integer'))
        )
    if triple_strings:
        lxr.setFlag('string-dbl-triple')
        lxr.setFlag('string-sgl-triple')
    return lxr


def readfile(path):
    with open(path, 'r') as ifstream: string = ifstream.read()
    return string


# Tests logic code
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

    def testRulesDoNotAcceptEmptyStrings(self):
        self.assertRaises(tartak.errors.EmptyRuleError, tartak.lexer.StringRule, group='foo', name='bar', pattern='')
        self.assertRaises(tartak.errors.EmptyRuleError, tartak.lexer.RegexRule, group='foo', name='bar', pattern='')

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
        self.assertEqual('integer', tokens[1].group())
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

    def testUnrecognizedSequencesConsumesOnlyInvalidSequenceAndNotFollowingString(self):
        variants = ['answer = $"42"',
                    'answer = $"""42\n"""',
                    "answer = $'42'",
                    "answer = $'''42'''",
                    ]
        for string in variants:
            lexer = getDefaultLexer(string)
            lexer._flags['string-dbl-triple'] = True
            lexer._flags['string-sgl-triple'] = True
            tokens = lexer.tokenize(errors='save').tokens()
            self.assertEqual('tartak', tokens[2].group())
            self.assertEqual('invalid', tokens[2].type())
            self.assertEqual('$', tokens[2].value())

    def testLexingSinglequotedString(self):
        string = "s = 'string'"
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('single', tokens[2].type())
        self.assertEqual('string', tokens[2].value())

    def testLexingDoublequotedString(self):
        string = 's = "string"'
        lexer = getDefaultLexer(string)
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('double', tokens[2].type())
        self.assertEqual('string', tokens[2].value())

    def testLexingTripleSinglequotedString(self):
        string = """s = '''string
        '''"""
        lexer = getDefaultLexer(string).setFlag('string-sgl-triple')
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('triple', tokens[2].type())
        self.assertEqual('string\n        ', tokens[2].value())

    def testLexingTripleDoublequotedString(self):
        string = '''s = """string
        """'''
        lexer = getDefaultLexer(string).setFlag('string-dbl-triple')
        tokens = lexer.tokenize(errors='save').tokens()
        self.assertEqual('string', tokens[2].group())
        self.assertEqual('triple', tokens[2].type())
        self.assertEqual('string\n        ', tokens[2].value())


class LexerExporterTests(unittest.TestCase):
    def testExportingStringRule(self):
        lxr = tartak.lexer.Lexer().append(tartak.lexer.StringRule(group='keyword', name='if', pattern='if'))
        self.assertEqual('token string keyword:if = "if";', lxr.export())

    def testExportingRegexRule(self):
        lxr = tartak.lexer.Lexer().append(tartak.lexer.RegexRule(group='integer', name='dec', pattern='(0|[1-9][0-9]*)'))
        self.assertEqual('token regex integer:dec = "(0|[1-9][0-9]*)";', lxr.export())


class LexerImporterTests(unittest.TestCase):
    def testImportingStringRule(self):
        variants = [
            'token string keyword:if = "if"; token string keyword:else = "else";',
            "token string keyword:if = 'if'; token string keyword:else = 'else';",
        ]
        lxr = (tartak.lexer.Lexer().append(tartak.lexer.StringRule(group='keyword', name='if', pattern='if'))
                                   .append(tartak.lexer.StringRule(group='keyword', name='else', pattern='else'))
               )
        for string in variants:
            self.assertEqual(lxr, tartak.lexer.Importer(string).make().lexer())

    def testImportingRegexRule(self):
        variants = [
            'token regex integer:dec = "(0|[1-9][0-9]*)";',
            "token regex integer:dec = '(0|[1-9][0-9]*)';",
        ]
        lxr = tartak.lexer.Lexer().append(tartak.lexer.RegexRule(group='integer', name='dec', pattern='(0|[1-9][0-9]*)'))
        for string in variants:
            self.assertEqual(lxr, tartak.lexer.Importer(string).make().lexer())

    def testImportingFlag(self):
        variants = [
            'flag string_dbl_triple = true;',
        ]
        lxr = tartak.lexer.Lexer()
        lxr.setFlag('string-dbl-triple', True)
        for string in variants:
            self.assertEqual(lxr, tartak.lexer.Importer(string).make().lexer())

    def testImportingBackslashRule(self):
        variants = [
            'token string backslash = "\\\\";',
        ]
        lxr = tartak.lexer.Lexer().append(tartak.lexer.StringRule(name='backslash', pattern='\\'))
        for string in variants:
            self.assertEqual(lxr, tartak.lexer.Importer(string).make().lexer())


class TokenStreamTests(unittest.TestCase):
    def testPointingChangesPositionOfTheCursor(self):
        string = '"foo" "bar" "baz" "bay" "bax"'
        lxr = getDefaultLexer().feed(string).tokenize()
        tokens = lxr.tokens()
        for tok in lxr.tokens():
            self.assertEqual(tokens[0], tok)
            tokens.point(1)
        self.assertEqual('foo', tokens.point(0, relative=False).get(0).value())

    def testPointingChangesReportedLengthOfStream(self):
        string = '"foo" "bar" "baz" "bay" "bax"'
        lxr = getDefaultLexer().feed(string).tokenize()
        tokens = lxr.tokens()
        for i in range(len(lxr.tokens()), 0, -1):
            self.assertEqual(i, len(tokens))
            tokens.point(1)
        self.assertEqual(5, len(tokens.point(0, relative=False)))

    def testPointingChangesValuesReturnedByIterator(self):
        string = '"foo" "bar" "baz" "bay" "bax"'
        lxr = getDefaultLexer().feed(string).tokenize()
        tokens = lxr.tokens().point(2)
        self.assertEqual(['baz', 'bay', 'bax'], [i.value() for i in tokens])

    def testPointingChangesReturnedCopy(self):
        string = '"foo" "bar" "baz" "bay" "bax"'
        lxr = getDefaultLexer().feed(string).tokenize()
        tokens = lxr.tokens()
        self.assertEqual(lxr.tokens(), tokens.copy())
        self.assertNotEqual(lxr.tokens(), tokens.copy().point(2).copy()) # we're copying twice to avoid pointing in original tokens

    def testPointingCanBeRewined(self):
        string = '"foo" "bar" "baz" "bay" "bax"'
        lxr = getDefaultLexer().feed(string).tokenize()
        tokens = lxr.tokens()
        self.assertEqual('foo', tokens.get(0).value())
        tokens.point(1)
        tokens.point(1)
        tokens.point(1)
        tokens.point(1)
        self.assertEqual('bax', tokens.get(0).value())
        tokens.rewind(0) # rewind to step 0
        self.assertEqual('foo', tokens.get(0).value())
        tokens.point(1)
        tokens.point(1)
        tokens.point(2)
        self.assertEqual('bax', tokens.get(0).value())
        tokens.rewind(-3) # rewind cursor to the position in which it was 3 .point()'s ago
        self.assertEqual('foo', tokens.get(0).value())
        tokens.point(4)
        self.assertEqual('bax', tokens.get(0).value())
        tokens.rewind(-200) # if the absolute value of a negative indexes is greater than length of the list of points, it results in rewinding the cursor to the beginning of the head
        self.assertEqual('foo', tokens.get(0).value())


class ParserSimpleMatchingTests(unittest.TestCase):
    def testMatchingByStringLiteral(self):
        string = '"foo"'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': None,
                    'not': False,
                    'value': 'foo',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 1)

    def testMatchingByTokenGroup(self):
        string = '"foo"'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 1)

    def testMatchingByTokenType(self):
        string = '"foo"'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 1)

    def testMatchingByFullTokenIdentifier(self):
        string = '"foo"'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 1)

    def testMatchingMultitokenRules(self):
        string = '"foo" \'bar\' """baz"""'
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [ # rule no. 1, by literal values
                {
                    'type': 'string',
                    'quantifier': None,
                    'not': False,
                    'value': 'foo',
                },
                {
                    'type': 'string',
                    'quantifier': None,
                    'not': False,
                    'value': 'bar',
                },
                {
                    'type': 'string',
                    'quantifier': None,
                    'not': False,
                    'value': 'baz',
                },
            ],
            [ # rule no. 2, by token group
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:',
                },
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:',
                },
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:',
                },
            ],
            [ # rule no. 3, by token type
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'double',
                },
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'single',
                },
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'triple',
                },
            ],
            [ # rule no. 4, by full token identifier
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:double',
                },
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:single',
                },
                {
                    'type': 'identifier',
                    'quantifier': None,
                    'not': False,
                    'value': 'string:triple',
                },
            ],
            [ # rule no. 5, by token group and quantifier *
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'string:',
                },
            ],
            [ # rule no. 6, by token group and quantifier +
                {
                    'type': 'identifier',
                    'quantifier': '+',
                    'not': False,
                    'value': 'string:',
                },
            ],
        ]
        for rule in variants:
            values = []
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 3)

    def testMatchingStringQuantifierStar(self):
        string = '"foo" "foo"'
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': '*',
                    'not': False,
                    'value': 'foo',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'string:',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'double',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'string:double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 2)

    def testMatchingStringQuantifierStarMayMatchNothing(self):
        string = ''
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': '*',
                    'not': False,
                    'value': 'foo',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'string:',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'double',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '*',
                    'not': False,
                    'value': 'string:double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 0)

    def testMatchingStringQuantifierPlus(self):
        string = '"foo" "foo"'
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': '+',
                    'not': False,
                    'value': 'foo',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '+',
                    'not': False,
                    'value': 'string:',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '+',
                    'not': False,
                    'value': 'double',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '+',
                    'not': False,
                    'value': 'string:double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 2)

    def testMatchingStringQuantifierPlusDoesNotMatchEmpty(self):
        string = ''
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': '+',
                    'not': False,
                    'value': 'foo',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '+',
                    'not': False,
                    'value': 'string:',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertFalse(matched)

    def testMatchingQuantifierQuestionMark(self):
        string = '"foo" "foo"'
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': '?',
                    'not': False,
                    'value': 'foo',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '?',
                    'not': False,
                    'value': 'string:',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '?',
                    'not': False,
                    'value': 'double',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '?',
                    'not': False,
                    'value': 'string:double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 1)

    def testMatchingQuantifierQuestionMarkMayMatchNothing(self):
        string = ''
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'string',
                    'quantifier': '?',
                    'not': False,
                    'value': 'foo',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '?',
                    'not': False,
                    'value': 'string:',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '?',
                    'not': False,
                    'value': 'double',
                },
            ],
            [
                {
                    'type': 'identifier',
                    'quantifier': '?',
                    'not': False,
                    'value': 'string:double',
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 0)


class ParserAlternativeMatchingTests(unittest.TestCase):
    def testMatchingSingleTokenAlternative(self):
        string = '"""foo"""'
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': None,
                    'not': False,
                    'value': [
                        {
                            'type': 'identifier',
                            'quantifier': None,
                            'not': False,
                            'value': 'string:single',
                        },
                        {
                            'type': 'identifier',
                            'quantifier': None,
                            'not': False,
                            'value': 'string:double',
                        },
                        {
                            'type': 'string',
                            'quantifier': None,
                            'not': False,
                            'value': 'foo',
                        },
                    ],
                },
            ]
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 1)

    def testMatchingSingleTokenAlternativeWithQuantifierStar(self):
        string = '"""foo""" "bar" \'baz\''
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': '*',
                    'not': False,
                    'value': [
                        {
                            'type': 'identifier',
                            'quantifier': None,
                            'not': False,
                            'value': 'string:single',
                        },
                        {
                            'type': 'identifier',
                            'quantifier': None,
                            'not': False,
                            'value': 'string:double',
                        },
                        {
                            'type': 'string',
                            'quantifier': None,
                            'not': False,
                            'value': 'foo',
                        },
                    ],
                },
            ]
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 3)

    def testMatchingSingleTokenAlternativeWithQuantifierPlus(self):
        string = '"""foo""" "bar" \'baz\''
        tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': '+',
                    'not': False,
                    'value': [
                        {
                            'type': 'identifier',
                            'quantifier': None,
                            'not': False,
                            'value': 'string:single',
                        },
                        {
                            'type': 'identifier',
                            'quantifier': None,
                            'not': False,
                            'value': 'string:double',
                        },
                        {
                            'type': 'string',
                            'quantifier': None,
                            'not': False,
                            'value': 'foo',
                        },
                    ],
                },
            ]
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            if not matched or DEBUG:
                print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
            self.assertTrue(matched)
            self.assertEqual(count, 3)

    def testMatchingGroupAlternative(self):
        strings = [
            '"foo" "bar"',
            '"lorem" "ipsum"'
        ]
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': None,
                    'not': False,
                    'value': [
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'lorem',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'ipsum',
                                },
                            ]
                        },
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'foo',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'bar',
                                },
                            ]
                        },
                    ],
                },
            ]
        ]
        for string in strings:
            tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
            parser = tartak.parser.Parser(getDefaultLexer())
            for rule in variants:
                matched, count = parser.matchrule(rule, tokens)
                if not matched or DEBUG:
                    print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
                self.assertTrue(matched)
                self.assertEqual(count, 2)

    def testMatchingGroupAlternativeWithQuantifierStar(self):
        strings = [
            '"foo" "bar" "lorem" """ipsum"""',
            '"lorem" "ipsum" """foo""" "bar"'
        ]
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': '*',
                    'not': False,
                    'value': [
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'lorem',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'ipsum',
                                },
                            ]
                        },
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'foo',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'bar',
                                },
                            ]
                        },
                    ],
                },
            ]
        ]
        for string in strings:
            tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
            parser = tartak.parser.Parser(getDefaultLexer())
            for rule in variants:
                matched, count = parser.matchrule(rule, tokens)
                if not matched or DEBUG:
                    print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
                self.assertTrue(matched)
                self.assertEqual(count, 4)

    def testMatchingGroupAlternativeWithQuantifierStarMayMatchNothing(self):
        strings = [
            'nope "foo" "bar" "lorem" """ipsum"""',
            'nope "lorem" "ipsum" """foo""" "bar"'
        ]
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': '*',
                    'not': False,
                    'value': [
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'lorem',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'ipsum',
                                },
                            ]
                        },
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'foo',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'bar',
                                },
                            ]
                        },
                    ],
                },
            ]
        ]
        for string in strings:
            tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
            parser = tartak.parser.Parser(getDefaultLexer())
            for rule in variants:
                matched, count = parser.matchrule(rule, tokens)
                if matched or DEBUG:
                    print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
                self.assertFalse(matched)
                self.assertEqual(count, 0)

    def testMatchingGroupAlternativeWithQuantifierPlus(self):
        strings = [
            '"foo" "bar" "lorem" """ipsum"""',
            '"lorem" "ipsum" """foo""" "bar"'
        ]
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': '+',
                    'not': False,
                    'value': [
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'lorem',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'ipsum',
                                },
                            ]
                        },
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'foo',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'bar',
                                },
                            ]
                        },
                    ],
                },
            ]
        ]
        for string in strings:
            tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
            parser = tartak.parser.Parser(getDefaultLexer())
            for rule in variants:
                matched, count = parser.matchrule(rule, tokens)
                if not matched or DEBUG:
                    print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
                self.assertTrue(matched)
                self.assertEqual(count, 4)

    def testMatchingGroupAlternativeWithQuantifierPlusMayNotMatchNothing(self):
        strings = [
            'nope "foo" "bar" "lorem" """ipsum"""',
            'nope "lorem" "ipsum" """foo""" "bar"'
        ]
        variants = [
            [
                {
                    'type': 'alternative',
                    'quantifier': '+',
                    'not': False,
                    'value': [
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'lorem',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'ipsum',
                                },
                            ]
                        },
                        {
                            'type': 'group',
                            'quantifier': None,
                            'not': False,
                            'value': [
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'foo',
                                },
                                {
                                    'type':         'string',
                                    'quantifier':   None,
                                    'value':        'bar',
                                },
                            ]
                        },
                    ],
                },
            ]
        ]
        for string in strings:
            tokens = getDefaultLexer(triple_strings=True).feed(string).tokenize().tokens()
            parser = tartak.parser.Parser(getDefaultLexer())
            for rule in variants:
                matched, count = parser.matchrule(rule, tokens)
                if matched or DEBUG:
                    print('{0}{1}'.format(('(DEBUG) ' if DEBUG and matched else ''), rule))
                self.assertFalse(matched)
                self.assertEqual(count, 0)


class ParserGroupMatchingTests(unittest.TestCase):
    def testMatchingGroup(self):
        string = 'var answer = 42;' # var leet = 1337;'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'group',
                    'quantifier': None,
                    'not': False,
                    'value': [
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        'var',
                        },
                        {
                            'type':         'identifier',
                            'quantifier':   None,
                            'value':        'name',
                        },
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        '=',
                        },
                        {
                            'type':         'identifier',
                            'quantifier':   None,
                            'value':        'integer:',
                        },
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        ';',
                        },
                    ]
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 5)

    def testMatchingGroupWithQuantifierStar(self):
        string = 'var answer = 42; var leet = 1337;'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'group',
                    'quantifier': '*',
                    'not': False,
                    'value': [
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        'var',
                        },
                        {
                            'type':         'identifier',
                            'quantifier':   None,
                            'value':        'name',
                        },
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        '=',
                        },
                        {
                            'type':         'identifier',
                            'quantifier':   None,
                            'value':        'integer:',
                        },
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        ';',
                        },
                    ]
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 10)

    def testMatchingGroupWithQuantifierPlus(self):
        string = 'var answer = 42; var leet = 1337;'
        tokens = getDefaultLexer().feed(string).tokenize().tokens()
        parser = tartak.parser.Parser(getDefaultLexer())
        variants = [
            [
                {
                    'type': 'group',
                    'quantifier': '+',
                    'not': False,
                    'value': [
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        'var',
                        },
                        {
                            'type':         'identifier',
                            'quantifier':   None,
                            'value':        'name',
                        },
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        '=',
                        },
                        {
                            'type':         'identifier',
                            'quantifier':   None,
                            'value':        'integer:',
                        },
                        {
                            'type':         'string',
                            'quantifier':   None,
                            'value':        ';',
                        },
                    ]
                },
            ],
        ]
        for rule in variants:
            matched, count = parser.matchrule(rule, tokens)
            self.assertTrue(matched)
            self.assertEqual(count, 10)


class ParserImporterTests(unittest.TestCase):
    @unittest.skip('TODO')
    def testImportingRule(self):
        string = 'rule float = intege:dec? "." integer:dec ("e" ("+" | "-")? integer:dec)?; rule number = float: | integer: ; rule literal = string: | number: ;'


if __name__ == '__main__':
    unittest.main()
