# Query Syntax

Assume that outputs should be maximized and inputs should be minimized. Also allow for constraints to turn specific things on or off. Always keep the syntax order the same. Use a symbol such as ? to indicate what you want the optimizer to maximize or minimize.

## Formal Query Syntax:

```ebnf
          <query_syntax> ::= <output_expr> | [<input_expr>]
                             | [<include_expr>] | [<exclude_expr>]
                             
           <output_expr> ::= <output_keyword> <outputs>
            <input_expr> ::= <input_keyword> <inputs>
          <include_expr> ::= <include_keyword> <includes>
          <exclude_expr> ::= <exclude_keyword> <excludes>
          
        <output_keyword> ::= "produce" | "make" | "create" | "output"
         <input_keyword> ::= "from" | "input" | "using"
       <include_keyword> ::= "with" | "including"
       <exclude_keyword> ::= "without" | "excluding"
           <and_keyword> ::= "and" | "+"
           <nor_keyword> ::= "and" | "or" | "nor"
           
               <outputs> ::= [<value_expr>] <output> [<and_keyword> <outputs>]
                <inputs> ::= [<value_expr>] <input> [and <inputs>]
              <includes> ::= <include_expr> [<and_keyword> <includes>]
              <excludes> ::= <exclude> [<nor_keyword> <excludes>]
              
            <value_expr> ::= ["only"] <value> |  "no"
          <include_expr> ::= [<include_modifier>] <include>
          
                <output> ::= <item_expr> | "power" | "tickets"
                 <input> ::= <item_expr> | <resource_expr> | "power" | "space"
                             | ["unweighted"] "resources" | "weighted resources"
               <include> ::= <recipe_expr> | <building_expr> 
                             | "alternate recipes" | "byproducts"
               <exclude> ::= <recipe_expr> | <building_expr> 
                             | "alternate recipes" | "byproducts"
                             
      <include_modifier> ::= "only" | "no" | "0"
                 <value> ::= <number> | <any_value> | <target> 
                <number> ::= "[0-9]+"
             <any_value> ::= "any" | "_"
                <target> ::= "?"
```

## Notes:
- Outputs, inputs, and constraints can be in any order. The parser will look
  for the keywords as delimiters between these expressions. However, an output
  is always required.
- The inverse constraints (`inv_constraints`) are only there to make the query
  more natural, but the same thing can be accomplished with regular constraints.
  For example `... with no alternate recipes and no fuel generators` is equivalent
  to `... without alternate recipes or fuel generators`.
- Byproduct handling still need to be figured out. One option is to try and find
  a solution without byproducts. If none exists, automatically find one with
  byproducts. This can also be explicitly controlled using the `byproducts`
  keyword in a constraint.
- The `only` keyword can be used in front of a `<value>` or `<constraint>` to
  indicate that all other entities of the same type should be disabled. For
  example, `produce ? iron plate from only 60 iron ore` will turn off all other
  resource inputs. The command `produce only power from 60 crude oil` would fail
  because there must be a byproduct.
- Ideally, the bot would be able to infer `?` or `_` in some contexts. For
  example, if no `?` is specified and there is one expression with an empty
  value, then assume that is the target. And if there is already a `?`
  specified, assume the others are `_`.
- The input `space` is a little strange since its not an input flow of material
  like the rest. However, it is an requirement to the produce chain and also
  something that the user may want to minimize. Also, the expression
  `using ? space` does have a natural meaning similar to `using ? <item>`.

## Examples
- Minimize resources to produce 60 iron plate per minute:
  ```
  produce 60 iron plate from ? resources
  ```
- Same thing, but the `from ? resources` is omitted since that is the default:
  ```
  produce 60 iron plate
  ```
- Maximize iron plate production from and input of 60 iron ore per minute.
  ```
  produce ? iron plate from 60 iron ore
  ```
- Max power from 240 crude oil per minute:
  ```
  produce ? power from 240 crude oil
  ```
- Same thing, but allowing for plastic as a byproduct:
  ```
  produce ? power and _ plastic from 240 crude oil
  ```
- Minimize space to produce 60 iron plate:
  ```
  produce 60 iron plate using ? space
  ```
- Minimize **weighted** resources to produce 60 iron plate:
  ```
  produce 60 iron plate from ? weighted resouces
  ```
- Disable alternate recipes:
  ```
  produce 60 iron plate without alternate recipes
  ```
- A different way of disabling alternate recipes:
  ```
  produce 60 iron plate with no alternate recipes
  ```
- Disable a building type:
  ```
  produce 60 iron plate without refineries
  ```
- Restrict power generation to only fuel generators:
  ```
  produce ? power from 60 crude oil with only _ fuel generators
  ```
- Restrict resource inputs to only iron ore:
  ```
  produce 60 iron plates from only iron ore
  ```
- Specify an non-resource input, such as 30 iron rods:
  ```
  produce 60 modular frames from ? resources and 30 iron rods
  ```
