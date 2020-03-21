# satisfoptimizer
A production calculator and optimizer for the video game Satisfactory. Available as a commandline tool or a discord bot.

## Windows Installation

*TODO*

1. Install python modules
```console
pip install -r requirements.txt
```

2. Install GraphViz:
 - Download from: https://www.graphviz.org/download/
 - Add install directory `C:\Program Files (x86)\Graphviz2.38\bin` to PATH
 
## Linux Installation

1. Install python3
```console
sudo apt-get install python3
```

2. Install pip
```console
sudo apt-get install python3-pip
```

3. Install GraphViz
```console
sudo apt-get install graphviz
```

4. Install git
```console
sudo apt-get install git
```

5. Clone repo (in directory of you choosing)
```console
git clone https://github.com/ScottJDaley/satisfoptimizer.git
```

6. Move inside the repo
```console
cd satisfoptimizer
```

6. Install python packages
```console
pip3 install -r requirements.txt
```
 
## How to run

### Command line tool

1. Double click `tool.py` to run it.
2. Enter one of the commands below
3. Type `!exit` to quit.

### Discord bot

1. Create a file called .env in source folder.
2. Add the following to the file:
   ```
   DISCORD_TOKEN={discord bot token}
   ```
   *Replace {discord bot token} with the token generated for the bot from the Discord developer portal.*
   
3. Double click `bot.py` to run the bot.
4. The bot should be able to respond to commands in Discord after a few seconds.
5. Press enter in the terminal to shut down the bot.

## Commands
The currently supported commands are:
 - `!min`: Minimize the resources required to produce some items.
 - `!max`: Maximize the production of an item.
 - `!items`: Get information about items.
 - `!recipes`: Get information about recipes.

### !min

Finds an optimal production chain that minimizes an objective while satisfying all constraints.

**Basic Usage:**
```
  !min iron-rod = 60
```

**Advanced Usage:**
```ebnf
  <syntax>             ::= "!min" [<objective> "where"] <constraints>
  <objective>          ::= <item> | <built_in_objective>
  <built_in_objective> ::= "unweighted-resources" | "weighted-resources" | "mean-weighted-resources"
  <constraints>        ::= <constraint> ["and" <constraints>]
  <constraint>         ::= <var_expr> <operator> <number>
  <operator>           ::= "=" | "<=" | ">="
  <var_expr>           ::= <var_glob> | <var>
  <var>                ::= <item_var> | <recipe> | <building>
  <item_var>           ::= [<prefix> ":"] <item>
  <prefix>             ::= <input> | <output>
```

**Notes:**
 - If the `<objective>` is ommitted, the `weighted-resources` objective is used by default.
 - An `<item_var>` such as `input:iron-rod` is used to express an input or iron rods that should be used in the production chain. Similary, `output:iron-rod` is used to express the desired output of a product.
 - An `<item>` can be used in place of an `<item_var>`. Resource items are interpreted as inputs while non-resource items are interpreted as outputs.

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
- produce 60/m iron rods without alternate recipes:
```
!min iron-rod = 60 and recipe:alternate* = 0
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

Finds an optimal production chain that maximizes an objective while satisfying all constraints.

**Basic Usage:**
```
  !max iron-rod where iron-ore <= 60
```

**Advanced Usage:**
```ebnf
  <syntax>             ::= "!max" <objective> "where" <constraints>
  <objective>          ::= <item>
  <constraints>        ::= <constraint> ["and" <constraints>]
  <constraint>         ::= <item_var> <operator> <number>
  <operator>           ::= "=" | "<=" | ">="
  <var_expr>           ::= <var_glob> | <var>
  <var>                ::= <item_var> | <recipe> | <building>
  <item_var>           ::= [<prefix> ":"] <item>
  <prefix>             ::= <input> | <output>
```

**Notes:**
 - An `<item_var>` such as `input:iron-rod` is used to express an input or iron rods that should be used in the production chain. Similary, `output:iron-rod` is used to express the desired output of a product.
 - An `<item>` can be used in place of an `<item_var>`. Resource items are interpreted as inputs while non-resource items are interpreted as outputs.

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
- iron rods where iron-ore <= 60 without alternate recipes:
```
!max iron-rod where iron-ore <= 60 and recipe:alternate* = 0
```

### !items

Get a list of all items or information about a particular item.

**Usage**
```ebnf
  <syntax> ::= "!items" [<item>]
```

**Examples:**
- List all items:
```
!items
```
- Get information about iron rods:
```
!items iron-rod
```

### !recipes

Get a list of all recipes, information about a recipe, or recipes for/using a particular item.

**Usage**
```ebnf
  <syntax>    ::= "!recipes" [<target>]
  <target>    ::= <recipe> | <for_item> | <using_item> | <building>
  <for_item>  ::= ["for"] <item>
  <using_item ::= "using" <item>
```

**Examples:**
- List all recipes:
```
!recipes
```
- Get information about the alternate recipe for iron ingots:
```
!recipes recipe:alternate-pure-iron-ingot
```
- Get information about recipes producing iron rod:
```
!recipes iron-rod
```
- Get information about recipes requiring iron rods as an ingredient:
```
!recipes using iron-rod
```
- Get information about all foundry recipes:
```
!recipes buildings:foundry
```

### !buildings

Get a list of all buildings or information about a particular building.

**Usage**
```ebnf
  <syntax> ::= "!buildings" [<buildings>]
```

**Examples:**
- List all buildings:
```
!buildings
```
- Get information about the foundry:
```
!buildings building:foundry
```

## Acknowledgements
The JSON data used by this program comes from Greeny's SatisfactoryTools
https://github.com/greeny/SatisfactoryTools
