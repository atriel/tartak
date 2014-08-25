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


class Rule:
    """Rule object that encapsulates pattern of single token.
    """
    def __init__(self, name, group, pattern):
        self._group, self._name = group, name
        self._pattern = pattern

    def getname(self):
        return self._group

    def getgroup(self):
        return self._group

    def match(self, string):
        """This method must be overridden in inheriting classes.
        Raise an exception if used directly.

        This method takes input string as a parameter and returns matched part of that string,
        or None if nothing was matched.
        """
        raise Exception('this method must be overridden')


class StringRule(Rule):
    """Object designed to match string rules.
    """
    def match(self, string):
        return (self._pattern if string.startswith(self._pattern) else None)


class RegexRule(Rule):
    """Object designed to match regex rules.
    """
    def __init__(self, *args):
        super(RegexRule, self).__init__(*args)
        self._regex = re.compile('^{0}'.format(pattern) if pattern[0] != '^' else pattern)

    def match(self, string):
        matched = self._regex.match(string)
        return (matched.groups(0) if matched is not None else None)


class Lexer:
    """Tokenizer class.
    """
    def __init__(self, string=''):
        self._rules = []
        self._line, self._char, self._charcount = 0, 0, 0
        self._tokens, self._raw = [], []
        self._string = string
        self._flags = {
            'string-single': True,
            'string-double': True,
            'string-dbl-triple': True,
            'string-sgl-triple': True,
        }

    def __iter__(self):
        return iter(self._tokens)

    def feed(self, s):
        self._string = s
        return self

    def append(self, rule):
        """Append rule to the list of rules.
        Accepts any object that has .match(str) method.
        """
        try:
            rule.match('')
        except:
            raise TypeError('{0} cannot be used as a rule'.format(type(rule)))
        self._rules.append(rule)
        return self

    def _stringmatch(self, s, quote):
        """Method that will match strings.
        """
        match = None
        n = len(quote)
        if s.startswith(quote):
            quote = s[:n]
            match = quote
            s = s[n:]
        closed = False
        while s:
            if s.startswith(quote) and not match.endswith('\\'):
                closed = True
                break
            match = s[0]
            s = s[1:]
        match = (match+quote if closed else None)
        return match

    def tokenize_old(self, strategy='default', errors='throw'):
        """Generate tokens from the string received.
        """
        string = self._string[:]
        while string:
            token, t_type, t_group = None, None, None
            if string[0] == '\n':
                string = string[1:]
                self._line += 1
                self._char = 0
                self._charcount += 1
                continue
            if string[0].strip() == '':
                string = string[1:]
                self._char += 1
                self._charcount += 1
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
            if string[0] == "'" and self._flags['string-single']:
                if DEBUG: print('token {0}: trying single-quoted string matching'.format(len(self._tokens)))
                token, t_type, t_group = self._stringmatch(string, "'"), 'string', 'double'
            if string[0] == '"' and self._flags['string-double']:
                if DEBUG: print('token {0}: trying double-quoted string matching'.format(len(self._tokens)))
                token, t_type, t_group = self._stringmatch(string, '"'), 'string', 'double'
            if string.startswith('"""') and self._flags['string-triple']:
                if DEBUG: print('token {0}: trying triple-quoted <{1}> string matching'.format(len(self._tokens), '"""'))
                token, t_type, t_group = self._stringmatch(string, '"""'), 'string', 'triple'
            if string.startswith("'''") and self._flags['string-triple']:
                if DEBUG: print('token {0}: trying triple-quoted <{1}> string matching'.format(len(self._tokens), "'''"))
                token, t_type, t_group = self._stringmatch(string, "'''"), 'string', 'triple'
            if token is None: raise Exception('string cannot be tokenized: {0}'.format(repr(string)))
            string = string[len(token):]
            if DEBUG and t_type == 'string': print('token {0} got cut to:'.format(repr(token)), end=' ')
            if DEBUG and t_type == 'string': print(repr(token))
            t = Token(line, char, t_type, value, t_group='')
            self._tokens.append(token)
            self._char += len(token.value())
            self._charcount += len(token.value())
        return self

    def tokenize(self, strategy='default', errors='throw'):
        """Generate tokens from the string received.
        """
        string = self._string[:]
        while string:
            token, t_type, t_group = None, None, None
            if string[0] == '\n':
                string = string[1:]
                self._line += 1
                self._char = 0
                self._charcount += 1
                continue
            if string[0].strip() == '':
                string = string[1:]
                self._char += 1
                self._charcount += 1
                continue
            if string[0] == "'" and self._flags['string-single']:
                if DEBUG: print('token {0}: trying single-quoted string matching'.format(len(self._tokens)))
                token, t_type, t_group = self._stringmatch(string, "'"), 'string', 'double'
            if string[0] == '"' and self._flags['string-double']:
                if DEBUG: print('token {0}: trying double-quoted string matching'.format(len(self._tokens)))
                token, t_type, t_group = self._stringmatch(string, '"'), 'string', 'double'
            if string.startswith('"""') and self._flags['string-dbl-triple']:
                if DEBUG: print('token {0}: trying triple-double-quoted <{1}> string matching'.format(len(self._tokens), '"""'))
                token, t_type, t_group = self._stringmatch(string, '"""'), 'string', 'triple'
            if string.startswith("'''") and self._flags['string-sgl-triple']:
                if DEBUG: print('token {0}: trying triple-single-quoted <{1}> string matching'.format(len(self._tokens), "'''"))
                token, t_type, t_group = self._stringmatch(string, "'''"), 'string', 'triple'
            if token is None:
                line = self._string.splitlines()[self._line]
                report =  'cannot tokenize sequence starting at line {0}, character {1}:\n'.format(self._line+1, self._char+1)
                report += line + '\n'
                report += '{0}^'.format('-'*self._char)
                raise Exception(report)
            string = string[len(token):]
            t = Token(line, char, t_type, value, t_group='')
            self._tokens.append(token)
            self._char += len(token.value())
            self._charcount += len(token.value())
        return self

    def tokens(self, raw=False):
        """Return generated tokens.
        """
        return (self._tokens if not raw else self._raw)
