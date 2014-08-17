## Tokenizer

Tartak tokenizer is highly versatile and flexible, and allows to tokenize most files.
It was tested on Python and C/C++ code, and has been used to tokenize some custom syntaxes.


----

### Rules

Tartak tokenizers are just sets of rules, which are applied to the beginning of a string
that is requested to be parsed.

Rules are checked against the string in the precise order in which they appear on the list.
The actual matching logic can be controlled by running tokenizer in different modes:

- `default`: Tartak stops trying them after first match.
- `inspect`: Tartak will accept first match but will continue checking for other matches and
             will report any potentially ambiguous tokens,
- `debug`:   same as `inspect` mode but instead of reporting and continuing with first match
             Tartak will raise and error about ambiguous tokens,
- `long`:    in this mode Tartak will try all the rules and accept one that yields longets match,


There are two types of rules that make Tartak tokenizers.
It is `regex` which states that rule should be matched using regular expressions, and
`string` which states that rule should be matched by simple comparison.


----

### Syntax

Rule files are composed using syntax defined here and may contain
statements, comments, directives and whitespace.
Comments and whitespace are ignored.
Statements define rules, directives are used to modify tokenizer internals (e.g. string-token handling).


#### Directive

Directive begins with an `@` character, followed by the directive name, followed by optional modifiers.

> Note: Developers are currently discouraged from using directives, or they may need to frequently
> change their tokenizer files.
> This is because the final syntax for directives has nnot yet been designed and
> directives may as well be absent in first releases of Tartak.

Examples:

```
@ruleenable string:triple

@ruledisable string:single, string:double
```


#### Comment

Comment begins with a `#` character.
Comments cannot appear after statements or directives.

Example:

```
# this is a comment
```


#### Statement

Every line that does not begin with a `#` or a `@` character and is not empty is considered a statement.
Statements end with the newline character.
Tartak can take only one statement per line.
Values of statements 

Examples:

```
# a regex statement with group and name
regex: foo: bar = "[1-9][0-9]*"

# a string statement without group (which becames the same as name)
string: answer = "42"
```


----

### String tokens

Tartak has built-in support (i.e. rules) for matching strings, because these rules would be hard to write and
matching strings is a very common task, and - as such - should be handled by the library instead of relying on users.
The included rules support getting tokens for following types of strings:

- single quoted: `'Hello "World"!'`,
- double quoted: `"Hello 'World"!"`,
- triple-quoted: `'''Hello 'beautiful' "World"!'''` or `"""Hello 'beautiful' "World"!"""` (known from Python),

First two types of strings are always present, and musy be explicitly disabled.
The triple quoted string support must be explicitly *enabled*.

All these tokens have `string` group and are named `single`, `double` and `triple`.
To match all strings in a parser pattern use `string:` expression; to match a specific type of string use
`string:single`, `string:double` or `string:triple` respectively.
However, you should rarely need the second form.


----

#### Whitespace tokens

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
- `\r` -- `whitespace:carriage`
