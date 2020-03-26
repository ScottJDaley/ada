## Query Syntax:

```ebnf
          <query_syntax> ::= <output_keyword> <outputs>
                             [<input_keyword> <inputs>]
                             [<constraint_keyword> <constraints>]
                             [<inv_constraint_keyword> <inv_constraints>]
                             
        <output_keyword> ::= "produce" | "make" | "create" | "output"
         <input_keyword> ::= "from" | "input"
    <constraint_keyword> ::= "with" | "using"
<inv_constraint_keyword> ::= "without" | "excluding"
           <and_keyword> ::= "and" | "+"
       <inv_and_keyword> ::= "and" | "or"
               <outputs> ::= <value> <output> [<and_keyword> <outputs>]
                <inputs> ::= <value> <input> [and <inputs>]
           <constraints> ::= <value> <constraint> [<and_keyword> <constraints>]
       <inv_constraints> ::= <constraint> [<inv_and_keyword> <inv_constraints>]
                <output> ::= <item_expr> | "power" | "tickets"
                 <input> ::= <item_expr> | <resource_expr> | "power"
                             | ["unweighted"] "resources" | "weighted resources"
            <constraint> ::= <recipe_expr> | <building_expr> | "space"
                             | "alternate recipes" | "byproducts"
                 <value> ::= ["only"] <value_expr>
            <value_expr> ::= <number> | <any_value> | <target> |  "no"
                <number> ::= "[0-9]+"
             <any_value> ::= "any" | "_"
                <target> ::= "?"
```

## Notes:
- The inverse constraints (`inv_constraints`) are only there to make the query
  more natural, but the same thing can be accomplished with regular constraints.
  For example `... with 0 alternate recipes and 0 fuel generators` is equivalent
  to `... without alternate recipes or fuel generators`.
- If a building is specified in a constraint with a value greater than 0, all
  other buildings of that type are turned off. 
- Byproduct handling still need to be figured out. One option is to try and find
  a solution without byproducts. If none exists, automatically find one with
  byproducts. This can also be explicitly controlled using the `byproducts`
  keyword in a constraint.
- The `only` keyword can be used in front of a `<value_expr>` to indicate that
  all other entities of the same type should be disabled. For example, `produce
  ? iron plate from only 60 iron ore` will turn off all other resource inputs. 
  The command `produce only power from 60 crude oil` would fail because there
  must be a byproduct.
- Ideally, the bot would be able to infer `?` or `_` in some contexts. For
  example, if no `?` is specified and there is one expression with an empty
  value, then assume that is the target. And if there is already a `?`
  specified, assume the others are `_`.

## Examples
- Max power from 240 crude oil:
  ```
  produce ? power from 240 crude oil
  ```
- Max power from 240 crude oil, allowing for plastic as a byproduct:
  ```
  produce ? power and _ plastic from 240 crude oil
  ```
- Minimize resources to produce 60 iron plate:
  ```
  produce 60 iron plate
  ```
- Minimize space to produce 60 iron plate:
  ```
  produce 60 iron plate with ? space
  ```
- Minimize weighted resources to produce 60 iron plate:
  ```
  produce 60 iron plate from ? weighted resouces
  ```
- Minimize resources to produce 60 iron plates without alternate recipes:
  ```
  produce 60 iron plate without alternate recipes
  ```
- Minimize resources to produce 60 iron plate without refineries:
  ```
  produce 60 iron plate without refineries
  ```
- Maximize power from 60 crude oil using fuel generators (no other generators):
  ```
  produce ? power from 60 crude oil with only _ fuel generators
  ```
- Minimize resources to produce 60 modular frames using 30 iron rods as input:
  ```
  produce 60 modular frames from ? resources and 30 iron rods
  ```
