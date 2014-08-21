#!/usr/bin/env python3

import mar

tknzr = mar.source.tokenizer.Tokenizer(flags=['MULTILINE_STRINGS'])
tknzr.addRule(name='comment', type='regex', pattern='#.*')
tknzr.addRule(name='keyword:import', type='string', pattern='import')
tknzr.addRule(name='name', type='regex', pattern='[A-Za-z_][A-Za-z0-9_]*')
tknzr.addRule(name='dot', type='string', pattern='.')
tknzr.addRule(name='comma', type='string', pattern=',')
tknzr.addRule(name='colon', type='string', pattern=':')
tknzr.addRule(name='assignment', type='string', pattern='=')
tknzr.addRule(name='lparen', type='string', pattern='(')
tknzr.addRule(name='rparen', type='string', pattern=')')
tknzr.addRule(name='l_square_bracket', type='string', pattern='[')
tknzr.addRule(name='r_square_bracket', type='string', pattern=']')


ifstream = open(__file__, 'r')
source = ifstream.read()
ifstream.close()

multiline_string = """#!/usr/bin/env python3

import mar"""

tknzr.feed(source)
tknzr.tokenize()

for i in tknzr.tokens(): print(i)
print()
print()
#for i in tknzr.tokens(raw=True): print(i)
#print()
#print()
print(''.join([token for line, pos, token in tknzr.tokens(raw=True)]))
