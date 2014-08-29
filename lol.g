list     = '[' elements ']' ;           // match bracketed list
elements = element (',' element)* ;     // match comma-separated list
element  = name | list ;                // element is name or nested list
