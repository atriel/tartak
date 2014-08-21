#!/usr/bin/env python3

"""Serialisation and deserialisation unit testing suite.
"""

import unittest
import warnings

import mar


DEBUG = False

SIMPLE_CASES = [
        ([('string', '?', 'import'), ('token', '', 'name'), ('string', '', ';')],
         '"import"? name ";"'),
        ([('string', '?', '::'), ('token', '', 'name'), ('group', '*', [('string', '', '::'), ('token', '', 'name')])],
         '"::"? name ("::" name)*'),
        ]


NESTED_GROUPS = (
    '"function" type? name lparen (type? modifier* name ("=" literal)? ",")* rparen',
    [('string', '', 'function'),
    ('token', '?', 'type'),
    ('token', '', 'name'),
    ('token', '', 'lparen'),
    ('group', '*', [
        ('token', '?', 'type'),
        ('token', '*', 'modifier'),
        ('token', '', 'name'),
        ('group', '?', [
            ('string', '', '='),
            ('token', '', 'literal')
        ]),
        ('string', '', ',')
    ]),
    ('token', '', 'rparen')
    ]
)


class SerialisationTests(unittest.TestCase):
    def testSerialisation(self):
        for pattern, expected in SIMPLE_CASES:
            got = mar.source.parser.serialise(pattern)
            self.assertEqual(expected, got)

    def testSerialisationOfNestedGroups(self):
        serialised, deserialised = NESTED_GROUPS
        got = mar.source.parser.serialise(deserialised)
        if DEBUG: print(got)
        self.assertEqual(serialised, got)


class DeserialisationTests(unittest.TestCase):
    def testDeserialisation(self):
        for expected, pattern in SIMPLE_CASES:
            got = mar.source.parser.deserialise(pattern)
            self.assertEqual(expected, got)

    def testDeserialisationOfNestedGroups(self):
        serialised, deserialised = NESTED_GROUPS
        got = mar.source.parser.deserialise(serialised)
        if DEBUG: print(got)
        self.assertEqual(deserialised, got)



if __name__ == '__main__': unittest.main()
