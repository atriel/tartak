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
        return '{0}:{1}({2}.{3}) :: {4}'.format(self._group, self._type, self._line, self._char, self._value)

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
        self._head = 0
        self._points = []

    def __len__(self):
        return len(self._tokens[self._head:])

    def __iter__(self):
        return iter(self._tokens[self._head:])

    def __getitem__(self, n):
        return self._tokens[self._head+n]

    def __eq__(self, other):
        if len(self) != len(other): return False
        eq = True
        for i, token in enumerate(other):
            eq = token == self.get(i)
            if not eq: break
        return eq

    @classmethod
    def new(self, n=1):
        return tuple([TokenStream() for i in range(n)])

    def point(self, at, relative=True):
        """At is an integer telling which token is to be considered *first* now.
        """
        self._head = ((self._head+at) if relative else at)
        self._points.append( (at-self._head) if relative else at )
        return self

    def rewind(self, n=-1):
        """Rewinds last call to .point().
        After a rewind point()'s after the selected index are lost, i.e. you cannot rewind a rewind.
        """
        if n < 0: n = len(self._points)+n
        if n > len(self._points): raise IndexError('could not rewind to step {0}'.format(n))
        self._head = self._points[n:][0]
        self._points = self._points[:n]
        return self

    def seek(self, at):
        return self.get(at)

    def get(self, at):
        """Returns token at given index.
        """
        return self._tokens[ (self._head+at if at >= 0 else at) ]

    def slice(self, n):
        """Returns slice of the stream.
        """
        stream = self.point(n).copy()
        self.rewind()
        return stream

    def append(self, token):
        """Append token to stream.
        """
        self._tokens.append(token)
        return self

    def pop(self, n=0):
        """Pops a token at given index.
        """
        return self._tokens.pop(0)

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

    def copy(self):
        """Return copy of current stream.
        """
        new = TokenStream()
        for token in self._tokens[self._head:]: new.append(token)
        return new

    def dumps(self):
        """Return list of tokens as dumped dictionaries.
        Used to serialize token streams.
        """
        return [token.dumps() for token in self]
