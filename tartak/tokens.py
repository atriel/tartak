#!/usr/bin/env python3

import re


# Token-related abstractions
class Token:
    """Simple token object.
    """
    def __init__(self, line, char, value, t_type, t_group=''):
        self._line, self._char = line, char
        self._group, self._type = t_group, t_type
        self._value = value

    def __str__(self):
        return self._value

    def __repr__(self):
        return '{0}{1}({2}.{3}) :: {4}'.format(self._group, self._type, self._line, self._char, self._value)

    def dumps(self):
        d = {
            'line': self._line,
            'char': self._char,
            't_group': self._group,
            't_type': self._type,
            'value': self._value,
        }
        return d

    def loads(self, d):
        """Loads token data from dict.
        """
        self._line, self._group = d['line'], d['group']
        self._group, self._type = d['group'], d['type']
        self._value = d['value']

    def line(self):
        return self._line

    def char(self):
        return self._char

    def group(self):
        return self._group

    def type(self):
        return self._type

    def value(self):
        return self._value


class TokenStream:
    """Class representing token streams used by Tartak.
    """
    def __init__(self, vector=()):
        """Vector is any object that can be iterated and
        yields Token objects during iteration.
        """
        self._tokens = ([t for t in vector] if vector else [])
        self._at = 0

    def __len__(self):
        return len(self._tokens)

    def __iter__(self):
        return iter(self._tokens)

    def __getitem__(self, n):
        return self._tokens[n]

    @classmethod
    def new(self, n=1):
        return tuple([TokenStream() for i in range(n)])

    def point(self, at):
        """At is an integer telling which token is to be considered *first* now.
        """
        self._at = at
        return self

    def seek(self, at):
        """Returns token at given index.
        """
        return self._tokens[ (self._at+at if at >= 0 else at) ]

    def append(self, token):
        """Append token to stream.
        """
        self._tokens.append(token)
        return self

    def remove(self, group=None, type=None):
        """Remove tokens from stream.
        """
        tokens = []
        for t in self._tokens:
            if group is not None and t.group() == group: continue
            if type is not None and t.type() == type: continue
            tokens.append(t)
        self._tokens = tokens
        return self

    def dumps(self):
        """Return list of tokens as dumped dictionaries.
        Used to serialize token streams.
        """
        return [token.dumps() for token in self]
