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


# New code begins here, above functions and classes SHOULD NOT be used

class Parser:
    def __init__(self, lexer):
        self._lexrules = lexer._rules
        self._rules = {}
        self._tokens = lexer._tokens

    @classmethod
    def cellmatch(self, cell, token):
        """Matches single cell of a rule to a token.
        """
        match = False
        if cell['type'] == 'identifier':
            t_group, t_type = (cell['value'].split(':') if ':' in cell['value'] else ('', cell['value']))
            if (t_group == token.group() if t_group else True) and (t_type == token.type() if t_type else True):
                match = True
            #print('matching by: match value: {0}:{1} == {2}:{3} ({4})'.format(t_group, t_type, token.group(), token.type(), match))
        elif cell['type'] == 'string':
            match = (cell['value'] == token.value())
            #print('matching by: match value: {0} == {1} ({2})'.format(repr(cell['value']), repr(token.value()), match))
        elif cell['type'] == 'alternative':
            for a in cell['value']:
                match = Parser.cellmatch(a, token)
                if match: break
        return match

    @classmethod
    def matchrule(self, rule, tokens):
        match = False
        i = 0
        for item in rule:
            quantifier = item['quantifier']
            if quantifier in [None, '+'] and i > len(tokens):
                raise errors.EndOfTokenStreamError('unexpected end of token stream')
            if quantifier is None:
                if item['type'] in ['string', 'identifier', 'alternative']:
                    match, count = Parser.cellmatch(item, tokens[i]), 1
                else:
                    match, count = Parser.matchrule(item['value'], tokens.slice(i))
                #elif item['type'] == 'alternative':
                #    count = 0
                #    for j, altrule in enumerate(item['value']):
                #        print('trying alternative {0}'.format(j+1))
                #        altmatch, count = Parser.matchrule([altrule], tokens.slice(i))
                #        if altmatch:
                #            print('matched!')
                #            break
                #    match = altmatch
                if match: i += count
            else:
                if quantifier in ['+', '?'] and i < len(tokens) and Parser.cellmatch(item, tokens[i]):
                    match = True
                    i += 1
                elif quantifier == '+':
                    match = False
                else:
                    match = True
                while match and quantifier != '?' and i < len(tokens) and Parser.cellmatch(item, tokens[i]): i += 1
            if not match: break
        return (match, i)

    @classmethod
    def consumerule(self, rule, tokens):
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
