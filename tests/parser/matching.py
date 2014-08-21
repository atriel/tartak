#!/usr/bin/env python3

"""Pattern matching unit testing suite.
"""

import unittest
import warnings

import mar


DEBUG = False


class StringMatchingTests(unittest.TestCase):
    def testSimpleMatch(self):
        variants = [
                ('"foo"', True, 1),
                ('', False, 0)
                ]
        pattern = '"foo"'
        rule = mar.source.parser.deserialize(pattern)
        for string, expected_match, expexted_no in variants:
            tknzr = mar.source.tokenizer.Tokenizer(string)
            tokens = tknzr.tokenize().tokens()
            print()
            match, no = mar.source.parser.match(rule, tokens)
            self.assertEqual(expected_match, match)
            self.assertEqual(expexted_no, no)

    def testQuantiferZeroOrOneMatch(self):
        variants = [
                ('"foo"', True, 1),
                ('', True, 0)
                ]
        pattern = '"foo"?'
        rule = mar.source.parser.deserialize(pattern)
        for string, expected_match, expexted_no in variants:
            tknzr = mar.source.tokenizer.Tokenizer(string)
            tokens = tknzr.tokenize().tokens()
            print()
            match, no = mar.source.parser.match(rule, tokens)
            self.assertEqual(expected_match, match)
            self.assertEqual(expexted_no, no)

    def testQuantiferZeroOrMoreMatch(self):
        variants = [
                ('', True, 0),
                ('"foo"', True, 1),
                ('"foo" "foo"', True, 2),
                ('"foo" "foo" "foo"', True, 3),
                ]
        pattern = '"foo"*'
        rule = mar.source.parser.deserialize(pattern)
        for string, expected_match, expexted_no in variants:
            tknzr = mar.source.tokenizer.Tokenizer(string)
            tokens = tknzr.tokenize().tokens()
            print()
            match, no = mar.source.parser.match(rule, tokens)
            self.assertEqual(expected_match, match)
            self.assertEqual(expexted_no, no)

if __name__ == '__main__': unittest.main()
