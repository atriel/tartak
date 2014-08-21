#!/usr/bin/env python3

import json
import sys
import re


DEBUG = False


class Token:
    """Simple token object.
    """
    def __init__(self, line, pos, value):
        self._line, self._pos = 0, 0
        self._value = value


class Tokenizer:
    """Tokenizer class.
    """
    def __init__(self, string=''):
        self._rules, self._order = {}, []
        self._line, self._pos, self._char = 0, 0, 0
        self._tokens, self._raw = [], []
        self._string = string

    def __iter__(self):
        return iter(self._tokens)

    def feed(self, s):
        self._string = s
        return self

    def addRule(self, name, rule, group='', type='string'):
        self._order.append(name)
        self._rules[name] = {'rule': rule, 'group': group, 'type': type}
        return self

    def _stringmatch(self, base):
        string, quote = '', base[0]
        string += quote
        base = base[1:]
        while base:
            string += base[0]
            if base[0] == quote and string[-2] != '\\': break
            base = base[1:]
        return string

    def step(self):
        return self

    def tokenize(self):
        """Generate tokens from the string received.
        """
        string = self._string[:]
        while string:
            token, t_type, t_group = None, None, None
            if string[0] == ' ':
                string = string[1:]
                continue
            if string[0] == '\n':
                string = string[1:]
                self._line += 1
                continue
            for i in self._order:
                if DEBUG: print('token {0}: trying rule: {1}'.format(len(self._tokens), i))
                rule = self._rules[i]
                match = False
                if rule['type'] == 'string' and string.startswith(rule['rule']):
                    token, match = rule['rule'], True
                if rule['type'] == 'regex' and re.compile(rule['rule']).match(string):
                    token, match = re.compile(rule['rule']).match(string).group(0), True
                if match:
                    t_type = i
                    t_group = rule['group']
                    break
            if string[0] in ['"', "'"]:
                if DEBUG: print('token {0}: trying string matching'.format(len(self._tokens)))
                token, t_type, t_group = self._stringmatch(string), 'string', 'string'
            if token is None: raise Exception('string cannot be tokenized: {0}'.format(repr(string)))
            string = string[len(token):]
            if DEBUG and t_type == 'string': print('token {0} got cut to:'.format(repr(token)), end=' ')
            token = (token if t_type != 'string' else token[1:-1])
            if DEBUG and t_type == 'string': print(repr(token))
            self._tokens.append( (self._line, t_type, t_group, token) )
        return self

    def tokens(self, raw=False):
        """Return generated tokens.
        """
        return (self._tokens if not raw else self._raw)
