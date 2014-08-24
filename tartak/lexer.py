#!/usr/bin/env python3

import json
import sys
import re


DEBUG = False


class Token:
    """Simple token object.
    """
    def __init__(self, line, char, t_type, value, t_group=''):
        self._line, self._char = 0, 0
        self._group, self._type = t_group, t_type
        self._value = value

    def __str__(self):
        return self._value

    def __repr__(self):
        return '{0}{1}({2}.{3}) :: {4}'.format(self._group, self._type, self._line, self._char, self._value)

    def line(self):
        return self._line

    def char(self):
        return self._char

    def pos(self):
        return (self._line, self._char)

    def group(self):
        return self._group

    def type(self):
        return self._type

    def value(self):
        return self._value


class Lexer:
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
