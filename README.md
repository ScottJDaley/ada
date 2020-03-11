# satisfoptimizer
A production calculator and optimizer for the video game Satisfactory. Available as a commandline tool or a discord bot.


## How to use
Currently supports two commands:

### !min

Minimize resource usage to produce something. Finds an optimal production chain that minimizes an objective while satisfying all constraints

**Usage:**
```
  !min [<objective> "where"] <constraints>
  
  <objective>          ::= <item> | <built-in-objective>
  <built-in-objective> ::= "unweighted-resources" | "weighted-resources" | "mean-weighted-resources"
  <constraints>        ::= <constraint> ["and" <constraints>]
  <constraint>         ::= <item-var> <operator> <number>
  <operator>           ::= "=" | "<=" | ">="
  <item-var>           ::= [<prefix> ":"] <item>
  <prefix>             ::= <input> | <output>
```

**Notes:**
 - If the <objective> is ommitted, the weighted-resources objective is used by default.
 - An <item-var> such as "input:iron-rod" is used to express an input or iron rods that should be used in the production chain. Similary, "output:iron-rod" is used to express the desired output of a product.
 - An <item> can be used in place of an <item-var>. Resource items are interpreted as inputs while non-resource items are interpreted as outputs.

**Examples:**
 
Find the most resource-efficient way to ...
- produce 60/m iron rods:
```
!min iron-rod = 60
```
- produce 60/m modular frames assuming there are 30\m iron rods available as input:
```
!min modular-frame = 60 and input:iron-rod = 30
```
- produce 600\m fuel, allowing for rubber as a byproduct:
```
!min fuel = 600 and rubber >= 0
```
- produce 60/m iron rods and 120/m iron plates:
```
!min  iron-rod = 60 and iron-plate = 120
```

Change the objective function:
- Minimize 60/m iron rods using unweighted resources:
```
!min unweighted-resources where iron-rod = 60
```
- Minimize rubber production from a fuel setup:
```
!min rubber where fuel = 600 and crude-oil <= 240 and water >= 0
```

### !max

Maximize production of something. Finds an optimal production chain that maximizes an objective while satisfying all constraints.

**Usage:**
```
  !max <objective> "where" <constraints>
  
  <objective>          ::= <item>
  <constraints>        ::= <constraint> ["and" <constraints>]
  <constraint>         ::= <item-var> <operator> <number>
  <operator>           ::= "=" | "<=" | ">="
  <item-var>           ::= [<prefix> ":"] <item>
  <prefix>             ::= <input> | <output>
```

**Notes:**
 - An <item-var> such as "input:iron-rod" is used to express an input or iron rods that should be used in the production chain. Similary, "output:iron-rod" is used to express the desired output of a product.
 - An {item} can be used in place of an {item-var}. Resource items are interpreted as inputs while non-resource items are interpreted as outputs.

**Examples:**
 
Maximize production of ...
- iron rods with only 60/m of iron ore:
```
!max iron-rod where iron-ore <= 60
```
- modular frames with only 60/m of iron ore assuming there are 30\m iron rods available as input:
```
!max modular-frame where iron-ore <= 60 and input:iron-rod = 30
```

- fuel from a pure crude oil node, allowing for rubber as a byproduct:
```
!max fuel where crude-oil <= 240 and rubber >= 0 and water >= 0
```

## Acknowledgements
The JSON data used by this program comes from Greeny's SatisfactoryTools
https://github.com/greeny/SatisfactoryTools
