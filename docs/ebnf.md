```ebnf
optimization*query ::= outputs inputs? includes? excludes?
ouputs ::= "produce" output ("and" output)*
inputs ::= "from" input ("and" input)*
includes ::= "with" include ("and" include)*
excludes ::= "without" exclude ("or" exclude)*
output ::= "only"? value output_var
input ::= "only"? value input_var
include ::= "only"? include_var
exclude ::= exclude_var
output_var ::= "power" | "tickets" | item_expr
input_var ::= "power" | "space" | ("unweighted"? "resources") | "weighted resources" | resource_expr | item_expr
include_var ::= recipe_expr | building_expr
exclude_var ::= "alternate recipes" | recipe_expr | building_expr
value ::= "?" | "*" | [0-9]+
item_expr ::= [a-fA-F]+
resource_expr ::= [a-fA-F]+
recipe_expr ::= [a-fA-F]+
building_expr ::= [a-fA-F]+
```

```ebnf
optimization*query ::= "produce" output ("and" output)* ("from" input ("and" input)*)? ("with" include ("and" include)*)? ("without" exclude ("or" exclude)*)?
output ::= "only"? value ("power" | "tickets" | item_expr)
input ::= "only"? value ("power" | "space" | ("unweighted"? "resources") | "weighted resources" | resource_expr | item_expr)
include ::= "only"? (recipe_expr | building_expr)
exclude ::= "alternate recipes" | recipe_expr | building_expr
value ::= "?" | "*" | [0-9]+
item_expr ::= [a-fA-F]+
resource_expr ::= [a-fA-F]+
recipe_expr ::= [a-fA-F]+
building_expr ::= [a-fA-F]+
```

```ebnf
optimization*query ::= ("produce" | "make" | "create") output (("and" | "+") output)*
("from" input (("and" | "+") input)*)?
(("with" | "using") include (("and" | "+") include)*)?
(("without" | "excluding") exclude ("or" exclude)*)?
output ::= "only"? value ("power" | "tickets" | item)
input ::= "only"? value ("power" | "space" | ("unweighted"? "resources") | "weighted resources" | resource | item)
include ::= "only"? (recipe | building)
exclude ::= "alternate recipes" | recipe | building
value ::= "?" | "*" | [0-9]+
```

```ebnf
optimization*query ::= outputs inputs? includes? excludes?
outputs ::= ("produce" | "make" | "create") ("only"? ("?" | "*" | [0-9]+) ("power" | "tickets" | item)) (("and" | "+") ("only"? ("?" | "_" | [0-9]+) ("power" | "tickets" | item)))\*
inputs ::= "from" ("only"? ("?" | "_" | [0-9]+) ("power" | "space" | ("unweighted"? "resources") | "weighted resources" | resource | item)) (("and" | "+") ("only"? ("?" | "\_" | [0-9]+) ("power" | "space" | ("unweighted"? "resources") | "weighted resources" | resource | item)))_
includes ::= ("with" | "using") ("only"? (recipe | building)) (("and" | "+") ("only"? (recipe | building)))_
excludes ::= ("without" | "excluding") ("alternate recipes" | recipe | building) ("or" ("alternate recipes" | recipe | building))\*
```
