## Parser

Parser is built from rules and operates on tokens and rules.

----

### Syntax

Rules in Tartak's parser are defined as follows:

```
Rule = name "=" Item+ ";"
```

Here, `name` means a sequence of alphanumeric characters not enclosed in
quotes beginning with a capital letter.

Parentheses can be used for grouping of items, e.g.:

```
List = "[" (Value ",")* "]" ;
```


----

### Modifiers

Following multiplicity modifiers are available:

- `*`: can appear zero or more times, suffix;
- `+`: can appear one or more times, suffix;
- `?`: can appear zero or one time, suffix;
- `!`: can appear zero times (can *not* appear), prefix;


----

### Matching rules and tokens.

Each rule is made up of different kinds of *items*, an item being a token, string, modifier or another rule.
