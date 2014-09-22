#!/usr/bin/env python3

import json
import sys
import re

from . import lexer, tokens, errors


DEBUG = False


def serialise(pattern):
    """Returns a string representation of rule pattern for parser.
    """
    serialised = ''
    for i, elem in enumerate(pattern):
        t_type, modifier, value = elem
        if t_type == 'token': serialised += value
        elif t_type == 'string': serialised += '"{0}"'.format(value)
        elif t_type == 'group': serialised += '({0})'.format(serialise(value))
        if modifier in ['?', '*', '+', '']: serialised += modifier
        else: raise SyntaxError('invalid modifier: {0}'.format(modifier))
        if i < len(pattern)-1: serialised += ' '
    return serialised

def _tokenize(pattern):
    lxr = lexer.Lexer()
    (lxr.append(tokens.RegexRule(name='token', pattern='[a-zA-Z][a-zA-Z0-9]*(-[a-zA-Z][a-zA-Z0-9]*)*', group='tokens', type='regex'))
        .append(tokens.StringRule(name='wildcart', pattern='*', group='quantifier', type='string'))
        .append(tokens.StringRule(name='optional', pattern='?', group='quantifier', type='string'))
        .append(tokens.StringRule(name='plus', pattern='+', group='quantifier', type='string'))
        .append(tokens.StringRule(name='lparen', pattern='(', group='parens', type='string'))
        .append(tokens.StringRule(name='rparen', pattern=')', group='parens', type='string'))
        )
    return lxr.feed(pattern).tokenize().tokens()

def _closingafter(tokens):
    """Returns number of tokens until the left parenthesis is closed.
    """
    n = 0
    opened = 1
    for i in tokens:
        if i[1] == 'lparen': opened += 1
        if i[1] == 'rparen': opened -= 1
        n += 1
        if opened == 0: break
    if opened: raise SyntaxError('unbalanced parenthesis')
    return n

def _parse(tokens):
    """Parses tokens during deserialisation process.
    """
    deserialised = []
    while tokens:
        print('tokens:', tokens)
        e_type, e_mod, e_value = None, '', None
        n = 1
        t_type, value = tokens[0][1], tokens[0][-1]
        if t_type in ['string', 'token']:
            e_type, e_value = t_type, value
        elif e_type is not None and t_type in ['optional', 'plus', 'wildcart']:
            e_mod = value
        elif t_type == 'lparen' and e_type is None:
            e_type = 'group'
            more = _closingafter(tokens[1:])
            n += more
            sub = tokens[1:more]
            e_value = _parse(sub)
        tokens = tokens[n:]
        if len(tokens):
            if tokens[0][1] in ['optional', 'plus', 'wildcart']:
                e_mod = tokens[0][3]
                tokens = tokens[1:]
        deserialised.append( (e_type, e_mod, e_value) )
    return deserialised

def deserialize(pattern):
    """Deerialises a string representation into a pattern usable by parser.
    """
    if type(pattern) is not str: raise TypeError('expoected string but got: {0}'.format(type(pattern)))
    tokens = _tokenise(pattern)
    deserialised = []
    err = None
    try: deserialised = _parse(tokens)
    except SyntaxError as e: err = e
    finally:
        if err is not None: raise type(err)('{0}: {1}'.format(str(err), pattern))
    return deserialised


def match(rule, tokens):
    """Tries to match rule to the beginning of the list of tokens and returns number of tokens matched.
    """
    matched, no = False, 0
    print('rule to match:', rule)
    origin = {}
    origin['tokens'], origin['rule'] = tokens[:], rule[:]
    while rule:
        # first, get modifier and, based on it, set minimal an maximal possible occurences
        # second, get type to know how to match patern to tokens (token? string? subpattern?)
        # third, get the actual value of the pattern and loop over tokens with it trying to match
        # if match cannot be found, follow to the next step of pattern or
        # fail, if this step of the pattern must be present
        print('rule[0]:', rule[0])
        e_type, e_mod, e_value = rule[0]
        if e_mod == '': min, max = 1, 1
        elif e_mod == '?': min, max = 0, 1
        elif e_mod == '*': min, max = 0, None
        elif e_mod == '+': min, max = 1, None
        else: raise SyntaxError('invalid quantifier: {0}'.format(e_mod))
        n = 0
        while (n < max if max is not None else True):
            if tokens:
                token = tokens[0]
                print('token:', token)
                t_type, t_value = token[1], token[-1]
            else:
                print('token:', None)
                t_type, t_value = None, None
            if t_type == e_type and t_value == e_value: pass
            else: break
            n += 1
            no += 1
            tokens = tokens[n:]
        if n >= min and (n <= max if max is not None else True): rule = rule[1:]
        else: break
    if rule == []: matched = True
    return (matched, no)


class OldParser:
    def __init__(self, tokens=[]):
        self._rules, self._order = {}, []
        self._tokens = tokens
        self._tree = []

    def addRule(self, name, pattern):
        self._rules[name] = pattern
        self._order.append(name)
        return self

    def _match(self, rule, tokens):
        matched = 0
        for p_type, mod, pattern in self._rules[rule]:
            submatch = 0
            if p_type == 'string':
                token = tokens[0][2]
                print('matching string "{0}" to token-string "{1}"'.format(pattern, token))
                submatch = int(pattern == token)
            elif p_type == 'token':
                token = tokens[0][1]
                print('matching token "{0}" to token-type "{1}"'.format(pattern, token))
                submatch = int(pattern == token)
            elif p_type == 'rule':
                print('matching rule "{0}" to token sequence beginning with: {1}'.format(pattern, tokens[:4]))
            if not submatch and mod not in ['?']: break
            tokens = tokens[submatch:]
            matched += 1
        match = (matched == len(self._rules[rule]))
        print('matched: {0}'.format(match))
        return match

    def _match2(self, rule, tokens):
        """Tries to match rule to the beginning of the list of tokens and returns number of tokens matched.
        """
        matched = 0
        i = 0
        print(rule)
        while i < len(rule):
            # first, get modifier and, based on it, set minimal an maximal possible occurences
            # second, get type to know how to match patern to tokens (token? string? subpattern?)
            # third, get the actual value of the pattern and loop over tokens with it trying to match
            # if match cannot be found, follow to the next step of pattern or
            # fail, if this step of the pattern must be present
            print('rule[i]:', rule[i])
            e_type, e_mod, e_value = rule[i]
            i += 1
        return matched

    def _apply(self, rule, tokens):
        return [], 3

    def parse(self):
        self._tree = []
        tokens = self._tokens[:]
        while tokens:
            match, rule = False, ''
            for i in self._order:
                match = self._match2(self._rules[i], tokens)
                if match:
                    rule = i
                    break
            if not match: raise Exception('unparseable (invalid?) syntax starting at line {0}: {1}'.format((tokens[0][0]+1), rebuild(getline(tokens[0][0], self._tokens))))
            part, n = self._apply(self._rules[rule], tokens)
            tokens = tokens[n:]
        return self


# New code begins here, above functions and classes SHOULD NOT be used
class Rule:
    def __init__(self):
        self._items = []

    def match(self, tokens):
        """Returns matched tokens, or None if rule does not match the beggining of token stream.
        """
        match = None
        # TODO: implement logic...
        return match

    def consume(self, tokens):
        """Returns two-tuple: (matched-tokens, rest-of-token-stream).
        Should be called after a successful call to .match() as it will modify token stream.
        """
        match = []
        # TODO: implement logic...
        tokens = tokens[len(match):]
        return (match, tokens)


class Parser:
    def __init__(self, lexer):
        self._lexrules = lexer._rules
        self._rules = {}
        self._tokens = lexer._tokens

    @classmethod
    def tryrule(self, rule, tokens):
        match = False
        i = 0
        for item in rule:
            quantifier = item['quantifier']
            if quantifier is None:
                if not tokens:
                    raise errors.EndOfTokenStreamError('unexpected end of token stream')
                if item['type'] == 'string':
                    match = (item['value'] == tokens[i].value())
                elif item['type'] == 'identifier' and ':' in item['value']:
                    t_group, t_type = item['value'].split(':')
                    match = ((t_group == tokens[i].group()) and (t_type == tokens[i].type() if t_type else True))
                elif item['type'] == 'identifier' and ':' not in item['value']:
                    match = item['value'] == tokens[i].type()
                #elif item['type'] == 'alternative':
                #    for j, altrule in enumerate(item['value']):
                #        match = Parser.tryrule(altrule, tokens[i:])
                #        if match: break
                if match: i += 1
            else:
                if quantifier == '+' and not tokens:
                    raise errors.EndOfTokenStreamError('unexpected end of token stream')
                if item['type'] == 'string':
                    if quantifier == '+' and item['value'] == tokens[i].value():
                        match = True
                        i += 1
                    else:
                        match = True
                    while match and tokens and i < len(tokens) and item['value'] == tokens[i].value(): i += 1
                elif item['type'] == 'identifier':
                    t_group, t_type = (item['value'].split(':') if ':' in item['value'] else ('', item['value']))
                    if quantifier == '+' and ((t_group == tokens[i].group() if t_group else True) and (t_type == tokens[i].type() if t_type else True)):
                        match = True
                        i += 1
                    else:
                        match = True
                    while match and tokens and i < len(tokens) and ((t_group == tokens[i].group() if t_group else True) and (t_type == tokens[i].type() if t_type else True)): i += 1
            if not match: break
        return (match, i)

    @classmethod
    def matchrule(self, rule, tokens):
        matched = []
        left = tokens.copy()
        for item in rule:
            if item['quantifier'] is None:
                if item['type'] == 'string':
                    match = (item['value'][0] == left[0].value())
                elif item['type'] == 'identifier' and ':' in item['value'][0]:
                    t_group, t_type = item['value'][0].split(':')
                    match = ((t_group == left[0].group()) and (t_type == left[0].type() if t_type else True))
                elif item['type'] == 'identifier' and ':' not in item['value'][0]:
                    match = item['value'][0] == left[0].type()
                else:
                    raise Exception('rule did not match')
                if match: matched.append(left.pop())
            elif item['quantifier'] == '*':
                sub = []
                if item['type'] == 'string':
                    while left and item['value'][0] == left[0].value():
                        sub.append(left.pop())
                elif item['type'] == 'identifier' and ':' in item['value'][0]:
                    t_group, t_type = item['value'][0].split(':')
                    while left and ((t_group == left[0].group()) and (t_type == left[0].type() if t_type else True)):
                        sub.append(left.pop())
                matched.extend(sub)
            elif item['quantifier'] == '+':
                if not left:
                    raise errors.EndOfTokenStreamError('unexpected end of token stream')
                sub = []
                if item['type'] == 'string':
                    if item['value'][0] == left[0].value(): sub.append(left.pop())
                    else: raise Exception('rule did not match')
                    while left and item['value'][0] == left[0].value(): sub.append(left.pop())
                elif item['type'] == 'identifier' and ':' in item['value'][0]:
                    t_group, t_type = item['value'][0].split(':')
                    if ((t_group == left[0].group()) and (t_type == left[0].type() if t_type else True)): sub.append(left.pop())
                    else: raise Exception('rule did not match')
                    while left and ((t_group == left[0].group()) and (t_type == left[0].type() if t_type else True)): sub.append(left.pop())
                matched.extend(sub)
        return (matched, left)
