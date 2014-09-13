#!/usr/bin/env python3

"""Frontend to the Tartak lexer.

SYNOPSIS:
    python3 tools/lexer.py --help
    python3 tools/lexer.py [--errors <mode>] <rules> <file> [<output>]
    python3 tools/lexer.py (--check-syntax | -S) <rules> <file> [<output>]


OPTIONS:
    -e, --errors <mode>     - tells how to handle errors (throw, save, drop)
    -S, --check-syntax      - just check if file can be lexed
    -h, --help              - display this message


USAGE:
    The lexer frontend takes a <file> and tokenizes it according to rules described by
    <rules>.
    The result of the lexing process is a JSON encoded list of tokens.

    The lexing stops the moment an end-of-file is reached, i.e. input string is exhausted, or
    the lexer encounters a sequence it cannot recognize.
    In the latter situation lexer report the error and tells where to look for it giving its full
    location (line and character position).

    The output is by default written to a file called "a.tokens".
    This behaviour can be overriden by specifying the <output> operand.
    If it is a path, lexer will check if it can create the output file by writing empty string to it;
    in case of error during lexing the file is removed.
    If the file cannot be created - lexer aborts.
    If the <output> operand is a single hyphen character "-" the output is written to standard output.


BUGS:
    Any bugs should be reported on Tartak's github page.
    This tool operates on Tartak version '{tartak_version}'.
"""

import glob
import json
import os
import sys

sys.path.insert(1, os.getcwd())

import clap


try:
    import tartak
except ImportError as e:
    print('fatal: cannot import backend: {0}'.format(e))
    print('note:  check if Tartak is correctly installed on your system (if it is, check your Python path)')
    exit(127)


base, filename = os.path.split(sys.argv.pop(0))
filename_ui = os.path.splitext(filename)[0] + '.json'

with open(os.path.join(base, filename_ui), 'r') as ifstream: model = json.loads(ifstream.read())

args = list(clap.formatter.Formatter(sys.argv).format())
command = clap.builder.Builder(model).insertHelpCommand().build().get()
parser = clap.parser.Parser(command).feed(args)
checker = clap.checker.RedChecker(parser)


try:
    err = None
    checker.check()
    fail = False
except clap.errors.MissingArgumentError as e:
    print('missing argument for option: {0}'.format(e))
    fail = True
except clap.errors.UnrecognizedOptionError as e:
    print('unrecognized option found: {0}'.format(e))
    fail = True
except clap.errors.ConflictingOptionsError as e:
    print('conflicting options found: {0}'.format(e))
    fail = True
except clap.errors.RequiredOptionNotFoundError as e:
    fail = True
    print('required option not found: {0}'.format(e))
except clap.errors.InvalidOperandRangeError as e:
    print('invalid number of operands: {0}'.format(e))
    fail = True
except clap.errors.UIDesignError as e:
    print('UI has design error: {0}'.format(e))
    fail = True
except Exception as e:
    print('fatal: unhandled exception: {0}: {1}'.format(str(type(e))[8:-2], e))
    fail, err = True, e
finally:
    if fail: exit(1)
    ui = parser.parse().ui().finalise()


if '--version' in ui:
    print('tartak version {0}'.format(tartak.__version__))
    exit(0)
if clap.helper.HelpRunner(ui=ui, program=filename).adjust(options=['-h', '--help']).run().displayed(): exit(0)


# Standard help/version stuff behind, actual logic begins here...

ui = ui.down() # go down a mode, into 'lex' mode
operands = ui.operands()
if len(operands) < 3: operands.append('a.tokens')

LEXER_RULES, INPUT, OUTPUT = operands
JUST_CHECK_SYNTAX = ('--syntax-check' in ui)

ERRORS = (ui.get('--errors') if '--errors' in ui else 'throw')

if ERRORS not in ['throw', 'save', 'drop']:
    print('fatal: unknown error handling mode: {0}'.format(ERRORS))
    exit(1)

if not os.path.isfile(INPUT):
    print('fatal: {0} does not point to a file'.format(repr(INPUT)))
    exit(1)

try:
    if OUTPUT != '-':
        ofstream = open(OUTPUT, 'w')
        ofstream.write('')
        ofstream.close()
    err = None
except Exception as e:
    err = e
finally:
    if err is not None:
        print('fatal: cannot create output file: {0}'.format(OUTPUT))
        exit(4)


lexer = tartak.lexer.Lexer()

if LEXER_RULES == 'py' or LEXER_RULES == 'python' or LEXER_RULES == 'default':
    lexer._flags['string-sgl-triple'] = True
    lexer._flags['string-dbl-triple'] = True

    lexer.append(tartak.lexer.RegexRule(name='comment', pattern='^#.*'))

    lexer.append(tartak.lexer.StringRule(group='keyword', name='import', pattern='import'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='from', pattern='from'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='if', pattern='if'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='elif', pattern='elif'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='else', pattern='else'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='def', pattern='def'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='class', pattern='class'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='while', pattern='while'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='for', pattern='for'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='return', pattern='return'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='yield', pattern='yield'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='break', pattern='break'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='continue', pattern='continue'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='lambda', pattern='lambda'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='raise', pattern='raise'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='try', pattern='try'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='except', pattern='except'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='finally', pattern='finally'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='with', pattern='with'))
    lexer.append(tartak.lexer.StringRule(group='keyword', name='as', pattern='as'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='noteq', pattern='!='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='eq', pattern='=='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='lte', pattern='<='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='gte', pattern='>='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='lt', pattern='<'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='gt', pattern='>'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='assplus', pattern='+='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='assminus', pattern='-='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='assmul', pattern='*='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='assdiv', pattern='/='))

    lexer.append(tartak.lexer.StringRule(group='operator', name='or', pattern='|'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='and', pattern='&'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='caret', pattern='^'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='linecont', pattern='\\'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='dot', pattern='.'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='comma', pattern=','))
    lexer.append(tartak.lexer.StringRule(group='operator', name='assign', pattern='='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='colon', pattern=':'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='semicolon', pattern=';'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='dblstar', pattern='**'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='plus', pattern='+'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='minus', pattern='-'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='star', pattern='*'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='div', pattern='/'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='modulo', pattern='%'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='anota', pattern='@'))

    lexer.append(tartak.lexer.StringRule(group='paren', name='lparen', pattern='('))
    lexer.append(tartak.lexer.StringRule(group='paren', name='rparen', pattern=')'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lsquare', pattern='['))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rsquare', pattern=']'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lcurly', pattern='{'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rcurly', pattern='}'))

    lexer.append(tartak.lexer.StringRule(group='boolean', name='false', pattern='False'))
    lexer.append(tartak.lexer.StringRule(group='boolean', name='true', pattern='True'))

    lexer.append(tartak.lexer.RegexRule(group='integer', name='dec', pattern='^(0|[1-9][0-9]*)'))

    lexer.append(tartak.lexer.RegexRule(name='name', pattern='^[a-zA-Z_][a-zA-Z0-9_]*'))
elif LEXER_RULES == 'c++' or LEXER_RULES == 'cpp' or LEXER_RULES == 'c++' or LEXER_RULES == 'c':
    lexer.append(tartak.lexer.RegexRule(group='comment', name='inline', pattern='^//.*'))
    lexer.append(tartak.lexer.RegexRule(group='comment', name='block', pattern='^/\*.*\*/'))

    lexer.append(tartak.lexer.StringRule(group='directive', name='include', pattern='#include'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='noteq', pattern='!='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='eq', pattern='=='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='lte', pattern='<='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='gte', pattern='>='))

    lexer.append(tartak.lexer.StringRule(group='operator', name='lt', pattern='<'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='gt', pattern='>'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='dblcolon', pattern='::'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='dot', pattern='.'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='comma', pattern=','))
    lexer.append(tartak.lexer.StringRule(group='operator', name='assign', pattern='='))
    lexer.append(tartak.lexer.StringRule(group='operator', name='colon', pattern=':'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='semicolon', pattern=';'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='plus', pattern='+'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='minus', pattern='-'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='star', pattern='*'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='div', pattern='/'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='modulo', pattern='%'))

    lexer.append(tartak.lexer.StringRule(group='operator', name='qmark', pattern='?'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='xmark', pattern='!'))

    lexer.append(tartak.lexer.StringRule(group='paren', name='lparen', pattern='('))
    lexer.append(tartak.lexer.StringRule(group='paren', name='rparen', pattern=')'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lsquare', pattern='['))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rsquare', pattern=']'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lcurly', pattern='{'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rcurly', pattern='}'))

    lexer.append(tartak.lexer.StringRule(group='type', name='void', pattern='void'))
    lexer.append(tartak.lexer.StringRule(group='type', name='int', pattern='int'))
    lexer.append(tartak.lexer.StringRule(group='type', name='char', pattern='char'))
    lexer.append(tartak.lexer.StringRule(group='type', name='float', pattern='float'))
    lexer.append(tartak.lexer.StringRule(group='type', name='double', pattern='double'))

    lexer.append(tartak.lexer.StringRule(group='keyword', name='if', pattern='if'))

    lexer.append(tartak.lexer.RegexRule(group='integer', name='dec', pattern='^(0|[1-9][0-9]*)'))

    lexer.append(tartak.lexer.RegexRule(name='name', pattern='^[a-zA-Z_][a-zA-Z0-9_]*'))
elif LEXER_RULES == 'lol':
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lsquare', pattern='['))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rsquare', pattern=']'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='comma', pattern=','))
    lexer.append(tartak.lexer.StringRule(group='operator', name='assign', pattern='='))
    lexer.append(tartak.lexer.RegexRule(name='name', pattern='^[a-zA-Z_][a-zA-Z0-9_]*'))
elif LEXER_RULES == 'json':
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lcurly', pattern='{'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rcurly', pattern='}'))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='lsquare', pattern='['))
    lexer.append(tartak.lexer.StringRule(group='bracket', name='rsquare', pattern=']'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='colon', pattern=':'))
    lexer.append(tartak.lexer.StringRule(group='operator', name='comma', pattern=','))
    lexer.append(tartak.lexer.RegexRule(group='integer', name='dec', pattern='^-?(0|[1-9][0-9]*)'))
else:
    if not os.path.isfile(LEXER_RULES):
        print('fatal: {0} does not point to a file and does not name a predefined set'.format(repr(LEXER_RULES)))
        exit(3)
    with open(LEXER_RULES, 'r') as ifstream:
        lexer = tartak.lexer.Importer().feed(ifstream.read()).make().lexer()
try:
    with open(INPUT, 'r') as ifstream: string = ifstream.read()
    lexer.feed(string).tokenize(errors=ERRORS)
    if not JUST_CHECK_SYNTAX:
        out = json.dumps(lexer.tokens().dumps())
        if OUTPUT == '-':
            print(out)
        else:
            with open(OUTPUT, 'w') as ofstream: ofstream.write(out)
except tartak.errors.LexerError as e:
    print('fail: {0}'.format(e))
    exit(4)
finally:
    pass
