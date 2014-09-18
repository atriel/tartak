#!/usr/bin/env python3

import re
import warnings

from .errors import LexerError, EmptyRuleError, ParserError
from .tokens import Token, TokenStream


DEBUG = False

# Rule-related abstarctions
class LexerRule:
    """Rule object that encapsulates pattern of single token.
    """
    def __init__(self, pattern, name, group=None):
        self._group, self._name = (group if group is not None else name), name
        if pattern == '': raise EmptyRuleError('pattern for cannot be empty -> {0}:{1} = {2}'.format(group, name, repr(pattern)))
        self._pattern = pattern
        self._type = None

    def __eq__(self, other):
        return self.data() == other.data()

    def type(self):
        return self._name

    def group(self):
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


# Exporting and importing lexer files (*.lexer)
class Exporter:
    def __init__(self, lexer):
        self._lexer = lexer
        self._string = ''

    def export(self):
        """Exports Lexer objects into .lexer files.
        """
        lines = []
        for r in self._lexer.rules():
            line = 'token {0} {1}:{2} = "{3}";'.format(('string' if type(r) == StringRule else 'regex'), r.group(), r.type(), r.pattern())
            lines.append(line)
        self._string = '\n'.join(lines)
        return self

    def str(self):
        """Return exported string.
        """
        return self._string


class Importer:
    def __init__(self, string=''):
        self._string = string
        self._lexer, self._made = None, None

    def feed(self, s):
        """Feed string to be imported as lexer rules.
        """
        self._string = s
        return self

    def _makelex(self):
        self._lexer = Lexer()
        (self._lexer.append(StringRule(group='keyword', name='token', pattern='token'))
                    .append(StringRule(group='keyword', name='flag', pattern='flag'))
                    .append(StringRule(group='type', name='string', pattern='string'))
                    .append(StringRule(group='type', name='regex', pattern='regex'))
                    .append(StringRule(group='bool', name='true', pattern='true'))
                    .append(StringRule(group='bool', name='false', pattern='false'))
                    .append(StringRule(group='operator', name='assign', pattern='='))
                    .append(StringRule(group='operator', name='semicolon', pattern=';'))
                    .append(StringRule(group='operator', name='colon', pattern=':'))
                    .append(StringRule(group='operator', name='percent', pattern=';'))
                    .append(RegexRule(group='name', name='name', pattern='[_a-zA-Z][_a-zA-Z0-9]*'))
                    .append(RegexRule(group='comment', name='line', pattern='#.*'))
         )

    def make(self):
        """Makes lexer from string.
        """
        self._makelex()
        self._made = Lexer()
        tokens = self._lexer.feed(self._string).tokenize().tokens().remove(group='comment')
        rules = []
        flags = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type() == 'token':
                t_group, t_name, t_class, t_pattern = None, None, None, None
                if i+1 < len(tokens) and tokens[i+1].type() in ['string', 'regex']:
                    if i+2 < len(tokens) and tokens[i+2].type() == 'name':
                        if i+3 < len(tokens) and tokens[i+3].type() == 'colon':
                            if i+4 < len(tokens) and tokens[i+4].type() == 'name':
                                if i+5 < len(tokens) and tokens[i+5].type() == 'assign':
                                    if i+6 < len(tokens) and tokens[i+6].group() == 'string':
                                        if i+7 < len(tokens) and tokens[i+7].type() == 'semicolon':
                                            t_group = tokens[i+2].value()
                                            t_name = tokens[i+4].value()
                                            t_class = tokens[i+1].value()
                                            t_pattern = tokens[i+6]
                                            i += 7
                        elif i+3 < len(tokens) and tokens[i+3].type() == 'assign':
                            if i+4 < len(tokens) and tokens[i+4].group() == 'string':
                                if i+5 < len(tokens) and tokens[i+5].type() == 'semicolon':
                                    t_group = tokens[i+2].value()
                                    t_name = tokens[i+2].value()
                                    t_class = tokens[i+1].value()
                                    t_pattern = tokens[i+4]
                                    i += 5
                if t_class is None:
                    msg = 'invalid syntax: starting on line {0}, character {1}\n'.format(token.line(), token.char())
                    msg += self._lexer.getline(token.line(), rebuild=True)
                    msg += '\n'
                    msg += '-'*token.char() + '^'
                    raise ParserError(msg)
                else:
                    t_pattern = t_pattern.value()
                    rule = (StringRule if t_class == 'string' else RegexRule)(pattern=t_pattern, name=t_name, group=t_group)
                    rules.append(rule)
            elif token.type() == 'flag':
                flag, value = None, None
                if tokens[i+1].type() == 'name':
                    if tokens[i+2].type() == 'assign' and tokens[i+2].group() == 'operator':
                        if tokens[i+3].group() in ['bool', 'string']:
                            if tokens[i+4].type() == 'semicolon':
                                flag = tokens[i+1].value().replace('_', '-')
                                if tokens[i+3].value() == 'true': value = True
                                elif tokens[i+3].value() == 'false': value = False
                                else:
                                    value = tokens[i+3].value()
                                i += 4
                if flag is None:
                    msg = 'invalid syntax: starting on line {0}, character {1}\n'.format(token.line(), token.char())
                    msg += self._lexer.getline(token.line(), rebuild=True)
                    msg += '\n'
                    msg += '-'*token.char() + '^'
                    raise ParserError(msg)
                else:
                    flags.append( (flag, value) )
            else:
                msg = 'invalid syntax: starting on line {0}, character {1}\n'.format(token.line(), token.char())
                msg += self._lexer.getline(token.line(), rebuild=True)
                msg += '\n'
                msg += '-'*token.char() + '^'
                raise ParserError(msg)
            i += 1
        for rule in rules: self._made.append(rule)
        for flag, value in flags: self._made.setFlag(flag, value)
        return self

    def lexer(self):
        return self._made



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
            'newline': '\n',
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

    def rules(self):
        """Returns lexer's list of rules.
        """
        return self._rules

    def _matchWhitespace(self, string):
        return (string and string[0].strip() == '')

    def _consumeWhitespace(self, string, indent=False):
        """Conusme whitespace and return trimmed string.
        """
        token, t_type, t_group = None, None, None
        while string and string[0].strip() == '':
            if string.startswith(self._flags['newline']):
                if token is not None:
                    self._raw.append(Token(self._line, self._char, token, t_type, t_group))
                    if indent: self._tokens.append(Token(self._line, self._char, token, t_type, t_group))
                token, t_type, t_group = self._flags['newline'], 'newline', 'whitespace'
                string = string[len(self._flags['newline']):]
                self._raw.append(Token(self._line, self._char, token, t_type, t_group))
                token, t_type, t_group = None, None, None
                self._line += len(self._flags['newline'])
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

    def _matchString(self, s, quote):
        """Method that will match strings.
        """
        match = None
        n = len(quote)
        original = s[:]
        if s.startswith(quote):
            match = quote
            s = s[n:]
        else:
            return match
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
                line = self._string.splitlines()[self._line]
                report =  'broken string on line {0}, character {1}:\n'.format(self._line+1, self._char+1)
                report += line + '\n'
                report += '{0}^'.format('-'*(self._char+(len(match) if match is not None else 1)))
                raise LexerError(report)
            if char == '\n' and  quote in ['"""', "'''"]:
                self._line += 1
                self._char = 0
            match += char
        match = (match if closed else None)
        return match

    def _matchAnyString(self, s):
        match = False
        for str_type_start, str_type_name in [('"""', 'string-dbl-triple'), ("'''", 'string-sgl-triple'), ('"', 'string-double'), ("'", 'string-single')]:
            if s.startswith(str_type_start) and self._flags[str_type_name]:
                if self._matchString(s, str_type_start) is not None:
                    match = True
                    break
        return match

    def _consumeString(self, s):
        token, t_type, t_group = None, None, None
        for str_type_start, str_type_name in [('"""', 'string-dbl-triple'), ("'''", 'string-sgl-triple'), ('"', 'string-double'), ("'", 'string-single')]:
            if s.startswith(str_type_start) and self._flags[str_type_name]:
                token, t_group, t_type = self._matchString(s, str_type_start), 'string', str_type_name[-6:]
                break
        return (t_group, t_type, token)

    def _matchRule(self, s):
        match = False
        for r in self._rules:
            if r.match(s) is not None:
                match = True
                break
        return match

    def _consumeRule(self, s):
        t_group, t_type, token = None, None, None
        for r in self._rules:
            token = r.match(s)
            if token is not None:
                t_type = r.type()
                t_group = r.group()
                break
        return (t_group, t_type, token)

    def _consumeInvalid(self, s, errors='throw'):
        t_group, t_type, token = None, None, None
        invalid = ''
        while (not self._matchRule(s) and not self._matchWhitespace(s) and not self._matchAnyString(s) and s):
            invalid += s[0]
            s = s[1:]
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
            string = self._consumeWhitespace(string, indent)
            if not string: break
            t_group, t_type, match = self._consumeString(string)
            if match is None: t_group, t_type, match = self._consumeRule(string)
            if match is None: t_group, t_type, match = self._consumeInvalid(string, errors)
            string = string[len(match):]
            if t_group == 'string':
                token = match.replace('\\n', '\n').replace('\\\\', '\\').replace('\\t', '\t').replace('\\r', '\r')
            else:
                token = match
            self._char += len(match)
            if t_group == 'string':
                if t_type in ['double', 'single']:
                    token = token[1:-1]
                else:
                    token = token[3:-3]
            if t_group == 'tartak' and t_type == 'drop': continue
            self._tokens.append(Token(self._line, self._char, token, t_type, t_group))
            self._raw.append(Token(self._line, self._char, match, t_type, t_group))
        return self

    def tokens(self, raw=False):
        """Return generated tokens.
        """
        return (self._tokens if not raw else self._raw)

    def getline(self, n, rebuild=False):
        """If rebuild is True, return string containing given line number.
        Else, return tokens found in this line.
        """
        toks = []
        if self._raw[-1].line() < n: return IndexError('line number too high: {0}'.format(n))
        for t in self._raw:
            if t.line() > n: break
            if t.line() == n: toks.append(t)
        if rebuild:
            line = ''.join([t.value() for t in toks])
        else:
            line = toks
        return line

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

    def export(self):
        """Exports lexer rules to string which can be written to a file.
        """
        return Exporter(self).export().str()
