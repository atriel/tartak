"""Module containing all Tartak-specific exceptions.
"""

class TartakError(Exception):
    pass


class LexerError(TartakError):
    pass


class EmptyRuleError(LexerError):
    pass


class ParserError(TartakError):
    pass

class EndOfTokenStreamError(ParserError):
    pass
