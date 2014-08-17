## Parser

Parser is built from rules and operates on tokens.

```
NAME = token ...
NAME = token "string" ...
NAME = group: token "string" ...
NAME = group:token group: token "string" ...
```

Patterns are gathered into groups that match different lists of tokens, but resolve to same name.
Parentheses can be used for grouping.

Modifiers:

- `*`: can appear zero or more times,
- `+`: can appear one or more times,
- `?`: can appear zero or one time,
- `!`: can appear zero times (can *not* appear),

----

Patterns are represented as dictionaries:

```
{
    "group":    name of the group
    "name":     name of this particular token sequence
    "type":     can be token, string or group
    "modifier": can be one of these: * + ? !
    "value":    actual sequence of tokens to match,

}
```


**TODO**:

- `group` can be made into a rule: `('group', mod, [tok, tok...])` -> `('rule', mod, name)`
