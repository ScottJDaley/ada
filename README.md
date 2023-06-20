[![Build Status](https://drone.kiwi-labs.net/api/badges/ScottJDaley/ada/status.svg)](https://drone.kiwi-labs.net/ScottJDaley/ada)

# ADA

![alt text](/images/checkmark.png "ADA")
> I am ADA, also known as Artificial Directory and Assistant, tasked to support pioneers, such as you, in their mission.
>
> ~ *ADA*

ADA is a Discord bot for the Satisfactory video game.

**[Invite to Server](https://discord.com/api/oauth2/authorize?client_id=687148652732743710&permissions=2147608640&scope=bot%20applications.commands)**

With ADA, you can browse information about items, recipes, and buildings within Discord. You can also ask ADA to
calculate an optimal production chains and produce visualizations.

![alt text](/images/examples/sample_usage.gif "Sample Usage")

ADA is also available as a command line tool.

## Query Syntax

### Information Query

Provides information about items, buildings, and recipes in the game.

#### Query Syntax

![alt text](/docs/railroad/info_query.svg "Info Query")

#### Notes

- Regexes can be used when specifying items, recipes, and buildings.

#### Examples

- `/ada iron rod`: Information about iron rods.
- `/ada recipe iron rod`: Information about the iron rod recipe.
- `/ada refinery`: Information about refineries.
- `/ada recipes for iron rod`: Browse all recipes for making iron rods.
- `/ada recipes from iron rods`: Browse all recipes with iron rods as an ingredient.
- `/ada recipes for refineries`: Browse all recipes available in refineries.
- `/ada recipes for iron.*`: Browse all recipes for items whose name starts with "iron".
- `/ada compare recipe iron rod`: Compare the iron rod recipe against all other recipes for iron rods.
- `/ada compare recipes for iron rod`: Compare all recipes that produce iron rods.
- `/ada ingredients for recipe iron rod`: Browse all ingredients in the iron rod recipe.
- `/ada products for recipe iron rod`: Browse all products in the iron rod recipe.

### Optimization Query

Finds an optimal production chain. Attempts to minimize inputs, maximize
outputs, and adhere to any given constraints.

#### Query Syntax

![alt text](/docs/railroad/optimization_query.svg "Optimization Query")

#### Notes

- Alternate recipes are disabled by default. They can be enabled by adding `alternate-recipes` to the input clause. For
  example, `/ada produce 10 modular frames from alternate-recipes`.
- Only one objective `?` can be provided in the entire query.
- If no inputs are specified, the optimizer will attempt to minimize
  unweighted resources. This is equivalent to an input of `from _ unweighted resources`.
- Using the `only` keyword in the output will prevent byproducts, but may produce an infeasible solution.
- Using the `only` keyword in the input will restrict the inputs for a specific category. For
  example `produce ? power from only coal and water and coal generators` will prevent any other items from being used as
  input besides coal and water because they both fall into the `item` category. However, it does not restrict the types
  of generators being used. To limit the inputs to only coal generators and prevent other generators from being used,
  add the `only` keyword in front of `coal generators`.

#### Examples

- `/ada produce 60 iron rod`: Produces exactly 60 iron rods while minimizing the input resources (evenly weighted).
- `/ada produce 60 iron rod from ? unweighted resources`: Same as above.
- `/ada produce 60 iron rod from ? weighted resources`: Similar to above, but weights resources by their frequency on
  the
  map.
- `/ada produce 60 iron rod from ? iron ore`: Produces exactly 60 iron rods while minimizing iron ore.
- `/ada produce 60 iron rod from only ? iron ore`: Produces exactly 60 iron rods from exclusively iron ore.
- `/ada produce 60 iron rod from only ? iron ore and _ coal and alternate-recipes`: Produces exactly 60 iron rods from
  exclusively iron ore and coal, but only minimizing iron ore. Alternate recipes are allowed.
- `/ada produce ? iron rods from 60 iron ore`: Produce as many iron rods as possible from 60 iron ore.
- `/ada produce ? iron rods from only 60 iron ore`: Produce as many iron rods as possible from exclusively 60 iron ore.
- `/ada produce ? iron rods from only 60 iron ore and water and alternate-recipes`: Produce as many iron rods as
  possible from exclusively 60 iron ore and water with alterate recipes allowed.
- `/ada produce ? power from 240 crude oil and only fuel generators`: Produce as much power as possible from only 240
  crude oil only using fuel generators (no other generators allowed).
- `/ada produce 60 modular frames without refineries`: Produce exactly 60 modular frames without using any refineries,
  minimizing unweighted resources.
- `/ada produce only ? iron rods from 10 constructors`: Produce as many iron rods as possible from 10 constructors.
- `/ada produce only ? iron rods from only 10 constructors and _ smelters`: Produce as many iron rods as possible from
  only 10 constructors and however many smelters.

## Hosting ADA yourself

> :warning: You do not need to host ADA yourself to use the bot. Use the link at the top of the readme to invite ADA to
> your server. These instructions are only for those interested in customizing ADA and/or hosting it themselves.

### Windows Installation

1. Download python 3 from https://www.python.org/downloads/

2. Install GraphViz:

    - Download from: https://www.graphviz.org/download/
    - Add install directory `C:\Program Files (x86)\Graphviz2.38\bin` to PATH

3. Run the following as admin to configure GraphViz:
   ```cmd
   dot -c
   ```

4. Clone repo (in directory of you choosing)
   ```cmd
   git clone https://github.com/ScottJDaley/ada.git
   ```

5. Move inside the repo
   ```cmd
   cd ada
   ```

6. Create virtual environment and activate it

   ```cmd
   py -m venv venv
   ```

7. Active the virtual environment
   ```cmd
   venv\Scripts\activate
   ```

   :bulb: You may deactivate the virtual environment with `deactivate`

8. Install python modules
   ```cmd
   py -m pip install -r requirements.txt
   ```

### MacOS Installation

1. Download and install [Homebrew](https://brew.sh/)

   :bulb: Make sure Hombrew's package lists are up-to-date with `brew update`

2. Install Python 3
   ```zsh
   brew install python3
   ```

3. Install GraphViz
   ```zsh
   brew install graphviz
   ```

4. Clone repo (in directory of you choosing)

   ```zsh
   git clone https://github.com/ScottJDaley/ada.git
   ```

   :bulb: MacOS might prompt you to download `Xcode Commandline Tools` the first time you use the `git` command

5. Move inside the repo
   ```zsh
   cd ada
   ```

6. Create python virtual environment and activate it
   ```zsh
   python3 -m venv venv && source venv/bin/activate
   ```

   :bulb: You may deactivate the virtual environment with `deactivate`

7. Install python requirements
   ```zsh
    pip install -r requirements.txt
   ```

8. Set up Discord bot
   ```zsh
   export DISCORD_TOKEN={token from discord developer portal}
   ```

### Linux Installation

1. Install python3
   ```bash
   sudo apt-get install python3
   ```

2. Install pip
   ```bash
   sudo apt-get install python3-pip
   ```

3. Install GraphViz
   ```bash
   sudo apt-get install graphviz
   ```

4. Install git
   ```bash
   sudo apt-get install git
   ```

5. Clone repo (in directory of you choosing)
   ```bash
   git clone https://github.com/ScottJDaley/ada.git
   ```

6. Move inside the repo
   ```bash
   cd ada
   ```

7. Create Virtual environment and activate it
   ```bash
   python3 -m venv venv && source venv/bin/acivate
   ```

   :bulb: You may deactivate the virtual environment with `deactivate`

8. Install python packages
   ```bash
   pip3 install -r requirements.txt
   ```

9. Set up Discord bot
   ```bash
   export DISCORD_TOKEN={token from discord developer portal}
   ```

### Discord Bot Usage

1. Run `bot.py`
2. Ensure the bot is running and was started with a valid `DISCORD_TOKEN` as described above.
3. Invite the bot to your server using a link generated from OAuth2 page on https://discord.com/developers/applications.
4. The bot should be able to respond to commands in Discord after a few seconds.
5. Press `Enter` in the terminal to shut down the bot.

### Command Line Tool Usage

1. Run `tool.py`.
2. Type a query and press Enter.
3. Type `exit` to quit.

## Acknowledgements

- Images are taken from the [Official Satisfactory Wiki](https://satisfactory.wiki.gg/Satisfactory_Wiki).

## Contributing

Feel free to send pull requests and submit new issues. You are also welcome to fork this repo to make your own changes.
