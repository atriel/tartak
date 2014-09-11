#!/usr/bin/env python3

import re
import warnings

from .errors import LexerError
from .tokens import Token, TokenStream


DEBUG = False

# Rule-related abstarctions
class LexerRule:
    """Rule object that encapsulates pattern of single token.
    """
    def __init__(self, pattern, name, group=None):
        self._group, self._name = (group if group is not None else name), name
        self._pattern = pattern
        self._type = None

    def __eq__(self, other):
        return self.data() == other.data()

    def ttype(self):
        return self._name

    def tgroup(self):
        return self._group

    def pattern(self):
        return self._pattern

    def match(self, string):
        """This method must be overridden in inheriting classes.
        Raise an exception if used directly.

        This method takes input string as a parameter and returns matched part of that string,
        or None if nothing was matched.
        """
        raise Exception('this method must be overridden')

    def data(self):
        """Returns a dict containing rule's data.
        """
        d = {
            'group': self._group,
            'name': self._name,
            'pattern': self._pattern,
            'type': self._type,
        }
        return d


class StringRule(LexerRule):
    """Object designed to match string rules.
    """
    _identifier_char = re.compile('[a-zA-Z0-9_]+')
    def __init__(self, *args, **kwargs):
        super(StringRule, self).__init__(*args, **kwargs)
        self._type = 'string'

    def match(self, string):
        match = (self._pattern if string.startswith(self._pattern) else None)
        if match is not None and self._identifier_char.match(self._pattern) is not None:
            n = len(string[len(match):])
            if n > 0 and self._identifier_char.match(string[len(match)]) is not None: match = None
        return match


class RegexRule(LexerRule):
    """Object designed to match regex rules.
    """
    def __init__(self, *args, **kwargs):
        super(RegexRule, self).__init__(*args, **kwargs)
        pattern = kwargs['pattern']
        self._regex = re.compile('^{0}'.format(pattern) if pattern[0] != '^' else pattern)
        self._type = 'regex'

    def match(self, string):
        matched = self._regex.match(string)
        return (matched.group() if matched is not None else None)


# Lexer
class Lexer:
    """Lexer class.
    """
    def __init__(self, string=''):
        self._rules = []
        self._line, self._char = 0, 0
        self._tokens, self._raw = TokenStream.new(2)
        self._string = string
        self._flags = {
            'string-single': True,
            'string-double': True,
            'string-dbl-triple': False,
            'string-sgl-triple': False,
        }

    def __iter__(self):
        return iter(self._tokens)

    def __eq__(self, other):
        eq_rules = self._rules == other._rules
        eq_flags = self._flags == other._flags
        return eq_rules and eq_flags

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

    def setFlag(self, flag, value=True):
        """Sets flag to specified value.
        """
        self._flags[flag] = value
        return self

    def _consumeWhitespace(self, string, indent=False):
        """Conusme whitespace and return trimmed string.
        """
        token, t_type, t_group = None, None, None
        while string and string[0].strip() == '':
            if string[0] == '\n':
                if token is not None:
                    self._raw.append(Token(self._line, self._char, token, t_type, t_group))
                    if indent: self._tokens.append(Token(self._line, self._char, token, t_type, t_group))
                token, t_type, t_group = string[0], 'newline', 'whitespace'
                string = string[1:]
                self._raw.append(Token(self._line, self._char, token, t_type, t_group))
                token, t_type, t_group = None, None, None
                self._line += 1
                self._char = 0
            elif string[0] == '\t':
                t_type, t_group = 'tab', 'whitespace'
                if token is None: token = string[0]
                else: token += string[0]
                string = string[1:]
                self._char += 1
            else:
                t_type, t_group = 'space', 'whitespace'
                if token is None: token = string[0]
                else: token += string[0]
                string = string[1:]
                self._char += 1
        if token is not None:
            self._raw.append(Token(self._line, self._char-1, token, t_type, t_group))
            if self._char - len(token) == 0 and indent: self._tokens.append(Token(self._line, self._char-1, token, t_type, t_group))
        return string

    def _stringmatch(self, s, quote):
        """Method that will match strings.
        """
        match = None
        n = len(quote)
        original = s[:]
        if s.startswith(quote):
            match = quote
            s = s[n:]
        closed = False
        for i, char in enumerate(s):
            if s[i:].startswith(quote):
                backs = 1
                while backs < len(s) and match[-backs].endswith('\\'): backs += 1
                if (backs-1) % 2 == 0:
                    match += quote
                    closed = True
                    break
            if char == '\n' and quote not in ['"""', "'''"]:
                report =  'broken string on line {0} (displaying 128 following characters)\n'
                report += '{0}'.format(original[:128])
                raise LexerError(report)
            if char == '\n' and  quote in ['"""', "'''"]:
                self._line += 1
                self._char = 0
            match += char
        match = (match if closed else None)
        return match

    def _stringconsume(self, s):
        token, t_type, t_group = None, None, None
        for str_type_start, str_type_name in [('"""', 'string-dbl-triple'), ("'''", 'string-sgl-triple'), ('"', 'string-double'), ("'", 'string-single')]:
            if s.startswith(str_type_start) and self._flags[str_type_name]:
                token, t_group, t_type = self._stringmatch(s, str_type_start), 'string', str_type_name[-6:]
                break
        return (t_group, t_type, token)

    def _getrulematch(self, s):
        match = False
        for r in self._rules:
            token = r.match(s)
            if token is not None:
                match = True
                break
        return match

    def _rulematch(self, s, errors='throw'):
        token, t_type, t_group = None, None, None
        invalid = ''
        while not self._getrulematch(s) and s:
            invalid += s[0]
            s = s[1:]
        if not invalid:
            for r in self._rules:
                token = r.match(s)
                if token is not None:
                    t_type = r.ttype()
                    t_group = r.tgroup()
                    break
        if token is None:
            if errors == 'save':
                t_group, t_type, token = 'tartak', 'invalid', invalid
            elif errors == 'drop':
                t_group, t_type, token = 'tartak', 'drop', invalid
            else:
                line = self._string.splitlines()[self._line]
                report =  'cannot tokenize sequence starting at line {0}, character {1}:\n'.format(self._line+1, self._char+1)
                report += line + '\n'
                report += '{0}^'.format('-'*self._char)
                raise LexerError(report)
        return (t_group, t_type, token)

    def tokenize(self, indent=False, errors='throw'):
        """Generate tokens from the string received.
        """
        string = self._string[:]
        while string:
            token, t_type, t_group = None, None, None
            string = self._consumeWhitespace(string, indent)
            if token is not None or not string: continue
            t_group, t_type, token = self._stringconsume(string)
            if token is None: t_group, t_type, token = self._rulematch(string, errors)
            string = string[len(token):]
            t = Token(self._line, self._char, token, t_type, t_group)
            self._char += len(t.value())
            if t_group == 'tartak' and t_type == 'drop': continue
            self._tokens.append(t)
            self._raw.append(t)
        return self

    def tokens(self, raw=False):
        """Return generated tokens.
        """
        return (self._tokens if not raw else self._raw)

    def dumps(self):
        """Return lexer state as JSON-serializable dict.
        """
        lxr = {
            'rules': [i.data() for i in self._rules],
            'flags': self._flags,
        }
        return lxr

    def loads(self, state):
        """Loads lexer state previously dumped to JSON.
        """
        for i in state['rules']:
            rule = (StringRule if i['type'] == 'string' else RegexRule)
            del i['type']
            self.append( rule(**i) )
        self._flags = state['flags']
        return self
