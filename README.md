# ADA
>I am ADA, also known as Artificial Directory and Assistant, tasked to support pioneers, such as you, in their mission.
>
> ~ *ADA*

ADA is a Discord bot for the Satisfactory video game.

With ADA, you can browse information about items, recipes, and buildings within Discord. You can also ask ADA to calculate an optimal production chains and produce visualizations.

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
- Only one objective `?` can be provided in the entire query.
- If no inputs are specified, the the optimizer will attempt to minimize
  unweighted resources. This is equivalent to an input of `from _ unweighted resources`.

#### Examples
 
**TODO**

### Information Query

**TODO**

## Acknowledgements
- Images are taken from the [Official Satisfactory Wiki](https://satisfactory.gamepedia.com/Satisfactory_Wiki).
