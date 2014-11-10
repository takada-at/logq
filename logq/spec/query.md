```
expr:
    expr OR expr
  | expr AND expr
  | NOT expr
  | boolean_primary

boolean_primary:
    column comparison_operator literal
  | function_call

comparison_operator: = | >= | > | <= | < | <> | !=

column:
  \$[a-zA-Z0-9\-_]+

function_call:
   funcname '(' arglist ')'

funcname:
  [a-zA-Z_] [a-zA-Z0-9\-_]*

arglist:
  arg
  | arglist ',' arg

args:
  literal
  | column

literal:
  string
  | number

string:
  "*"
  | '*'

number:
  [0-9]+
```