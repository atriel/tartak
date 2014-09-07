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


# helper functions
def getDefaultLexer():
    lxr = tartak.lexer.Lexer()
    lxr.append(tarta.lexer.StringRule(pattern='', name='', group='')
    return lxr


class LexerTests(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
