## Lexer

Tartak lexer is highly versatile and flexible, and allows to tokenize most files.
It was tested on Python and C/C++ code, and has been used to tokenize some custom syntaxes.


----

### Rules

Tartak lexers are just sets of rules, which are applied to the beginning of a string
that is requested to be parsed.
Each rule generated one token type.


#### Rule types

There are two types of rules that make Tartak lexers.
It is `regex` which states that rule should be matched using regular expressions, and
`string` which states that rule should be matched by simple comparison.


#### Rule syntax

Syntax for defining a rule:

```
"token" ("string" | "regex") group? type = string-pattern+ ;
```

Rule definition begins with the `token` keyword,
followed by either `string` or `regex` keyword (to give the exact type of the rule),
followed by optional group,
followed by name of the token type being defined,
followed by assignment operator,
followed by pattern to match given as at least one string.  
When the group is omitted, it is the same as type.

The possibility of defining a pattern in multiple strings is provided as a helper mechanism,
to e.g. enable splitting particularly complex regular expressions to ease their understanding.
These strings are concatenated when the rule is created.


*Examples:*

```
# for string rule
token string keyword if = "if" ;

# for regex rule
token regex integer octal = "0o[0-7]+" ;

# with string concatenation
token regex integer hex = "0x"
                          "["
                              "0-9"
                              "a-f"
                              "A-F"
                          "]"
                          +"
                          ;
```


#### Rule matching

Rules are checked against the input string in the precise order in which they appear on the list.
The actual matching logic can be controlled by running lexer in different modes:

- *default*: Tartak stops trying after first match;
- *long*:    in this mode Tartak will try all the rules and accept one that yields longets match;
- *inspect*: Tartak will accept first match but will continue checking for other matches and
             will report any potentially ambiguous tokens;
- *debug*:   same as *inspect* mode but instead of reporting and continuing with first match
             Tartak will raise and error about ambiguous tokens;

By default, Tartak stops lexing the moment it finds a sequence of characters it cannot match.
However, it can be told to go on and do not stop on errors;
in such an event, lexer can be told to do different things with the error-causing characters:

- *save*:   this tells Tartak to save the error-causing characters as a token, and leave it on the
            token list, you should check the source code for the exact group and type of these tokens
            but it ought to be `tartak:unrec`;
- *drop*:   this tells Tartak to drop error-causing characters and go on like if nothing happened at all,
            such cavalier behaviour (to put it mildly) can be dangerous and lead to errors;

The *save* method can be particularly helpful because it will extract the illegal tokens from source text and
provide their exact locations, so they can be reported and removed from the source text.


----


### Comments

Comments begin with the hash character `#` and end with newline.
A few examples of comments:

```
# this is a comment

token regex integer octal = "0o[0-7]+" ; # this is also a comment

token regex integer hex = "0x"           # comments can be also
                          "["            # inserted like this
                            "0-9a-fA-F"  # to, for example,
                          "]"            # comment on different
                          "+"            # parts of regular expressions
                          ;
```


----

### Directives

Directive begins with an `@` character, followed by the directive name, followed by optional modifiers.

> Note: Developers are currently discouraged from using directives, or they may need to frequently
> change their lexer files.
> This is because the final syntax for directives has not yet been designed and
> directives may as well be absent in first releases of Tartak.

Examples:

```
@enable-string-triple   # to enable triple-string tokenization
@matching-mode-long     # to set matching mode inside the lexer file
@error-mode-save        # to set error handling mode to save
```


----

### Built-in token types

#### String

Tartak has built-in support for matching string tokens.
This includes support for getting tokens for following types of strings:

- single quoted: `'Hello "World"!'`,
- double quoted: `"Hello 'World"!"`,
- triple-quoted: `'''Hello 'beautiful' "World"!'''` or `"""Hello 'beautiful' "World"!"""` (known from Python),

First two types of strings are always present, and musy be explicitly disabled.
The triple quoted string support must be explicitly *enabled*.

All these tokens have `string` group and are named `single`, `double` and `triple`.
To match all strings in a parser pattern use `string:` expression; to match a specific type of string use
`string:single`, `string:double` or `string:triple` respectively.
However, you should rarely need the second form.


#### Whitespace

Whitespace is considered irrelevant and is removed from the token list.
The only whitespace characters Tartak thinks are important are newline characters and
they are used to increment line counter.

The *raw* token list is used to store all tokens (whitespace included) in case it is needed for diagnostic messages or
file rebuilding.
Joining raw tokens with empty string should yield exact copy of the string being tokenized.

All whitespace tokens are in `whitespace` group, and specific characters are named accordingly:

- ` `  -- `whitespace:space`,
- `\n` -- `whitespace:newline`,
- `\t` -- `whitespace:tab`,
- `\r` -- `whitespace:return`
