# ADA
>I am ADA, also known as Artificial Directory and Assistant, tasked to support pioneers, such as you, in their mission.
>
> ~ *ADA*

ADA is a Discord bot for the Satisfactory video game.

With ADA, you can browse information about items, recipes, and buildings within Discord.

![alt text](/images/examples/item_info.png "Item Info")

![alt text](/images/examples/recipes_for.png "Item Info")

You can also ask ADA to calculate an optimal production chains and produce visualizations.

![alt text](/images/examples/optimization.png "Item Info")

ADA is also available as a command line tool.

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
git clone https://github.com/ScottJDaley/ada.git
```

6. Move inside the repo
```console
cd satisfoptimizer
```

6. Install python packages
```console
pip3 install -r requirements.txt
```

7. Set up Discord bot
```console
echo "DISCORD_TOKEN={token from discord developer portal}" > .env
```
 
## How to run

### Command line tool

1. Double click `tool.py` to run it.
2. Type a query and press Enter.
3. Type `exit` to quit.

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

## Query Syntax

### Information Query

Provides information about items, buildings, and recipes in the game.

#### Query Syntax
![alt text](/images/rr_diagram/information_query.png "Information Query")

#### Entity Query
![alt text](/images/rr_diagram/entity_query.png "Entity Query")

#### Recipes For Query
![alt text](/images/rr_diagram/recipes_for_query.png "Recipes For Query")

#### Recipes From Query
![alt text](/images/rr_diagram/recipes_from_query.png "Recipes From Query")

#### Notes
- Regexes can be used when specifying items, recipes, and buildings.

#### Examples

- `ada iron rod`: Information about iron rods.
- `ada recipes for iron rod`: All recipes for making iron rods.
- `ada recipes from iron rods`: All recipes with iron rods as an ingredient.
- `ada recipes for refineries`: All recipes available in refineries.
- `ada recipes for iron.*`: All recipes for items whose name starts with "iron".

### Optimization Query

Finds an optimal production chain. Attempts to minimize inputs, maximize
outputs, and adhere to any given constraints.

#### Query Syntax
![alt text](/images/rr_diagram/optimization_query.png "Optimization Query")

#### Outputs
![alt text](/images/rr_diagram/outputs.png "Outputs")

#### Inputs
![alt text](/images/rr_diagram/inputs.png "Inputs")

#### Includes
![alt text](/images/rr_diagram/includes.png "Includes")

#### Excludes
![alt text](/images/rr_diagram/excludes.png "Excludes")

#### Notes
- Regexes can be used when specifying items, recipes, and buildings.
- Only one objective `?` can be provided in the entire query.
- If no inputs are specified, the the optimizer will attempt to minimize
  unweighted resources. This is equivalent to an input of `from _ unweighted resources`.

#### Examples
- `ada produce 60 iron rod from ? iron ore`: Produces exactly 60 iron rods while minimizing iron ore.
- `ada produce ? iron rods from 60 iron ore`: Produce as many iron rods as possible from 60 iron ore.
- `ada produce ? power from 240 crude oil with only fuel generators`: Produce as much power as possible from only 240 crude oil only using fuel generators (no other generators allowed).
- `ada produce 60 modular frames without refineries`: Produce exactly 60 modular frames without using any refineries, minimizing unweighted resources.

## Acknowledgements
- Images are taken from the [Official Satisfactory Wiki](https://satisfactory.gamepedia.com/Satisfactory_Wiki).
