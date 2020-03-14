import os
import discord
from satisfaction import Satisfaction

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

satisfaction = Satisfaction()

bot = commands.Bot(command_prefix='!')

async def send_message(ctx, msg):
  DISCORD_MESSAGE_LIMIT = 2000
  while len(msg) > DISCORD_MESSAGE_LIMIT:
    newline_index = msg.rfind('\n', 0, DISCORD_MESSAGE_LIMIT)
    await ctx.send(msg[:newline_index])
    msg = msg[newline_index:]
  await ctx.send(msg)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
           print('Unhandled message', args[0])
        else:
            raise


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

min_help = """Minimize resource usage to produce something

Finds an optimal production chain that minimizes an objective while satisfying all constraints

Usage:
  !min [{objective} where] {constraints}
  {objective} = {item|built-in-objective}
  {built-in-objective} = 'unweighted-resources' or 'weighted-resources' or 'mean-weighted-resources'
  {constraints} = {constraint} [and {constraints}]
  {constraint} = {item-var} {operator} {number}
  {operator} = '=' or '<=' or '>='
  {item-var} = {input|output}:{item}

Notes:
 - If the {objective} is ommitted, the weighted-resources objective is used by default.
 - An {item} can be used in place of an {item-var}. Resource items are interpreted as inputs while non-resource items are interpreted as outputs.

Examples:
 
  Find the most resource-efficient way to ...

    - produce 60/m iron rods:
      !min iron-rod = 60

    - produce 60/m modular frames assuming there are 30\m iron rods available as input:
      !min modular-frame = 60 and input:iron-rod = 30

    - produce 600\m fuel, allowing for rubber as a byproduct:
      !min fuel = 600 and rubber >= 0

    - produce 60/m iron rods and 120/m iron plates:
      !min  iron-rod = 60 and iron-plate = 120

  Change the objective function:

    - Minimize 60/m iron rods using unweighted resources:
      !min unweighted-resources where iron-rod = 60
    
    - Minimize rubber production from a fuel setup:
      !min rubber where fuel = 600 and crude-oil <= 240 and water >= 0
"""

max_help = """Maximize production of something

Finds an optimal production chain that maximizes an objective while satisfying all constraints.

Usage:
  !max {objective} where {constraints}
  {objective} = {item}
  {constraints} = {constraint} [and {constraints}]
  {constraint} = {item-var} {operator} {number}
  {operator} = '=' or '<=' or '>='
  {item-var} = {input|output}:{item}

Notes:
 - An {item} can be used in place of an {item-var}. Resource items are interpreted as inputs while non-resource items are interpreted as outputs.

Examples:
 
  Maximize production of ...

    - iron rods with only 60/m of iron ore:
      !max iron-rod where iron-ore <= 60

    - modular frames with only 60/m of iron ore assuming there are 30\m iron rods available as input:
      !max modular-frame where iron-ore <= 60 and input:iron-rod = 30

    - fuel from a pure crude oil node, allowing for rubber as a byproduct:
      !max fuel where crude-oil <= 240 and rubber >= 0 and water >= 0
"""

items_help = """Print item details

!items

!items iron-rod
"""

recipes_help = """Print recipes details

!recipes

!recipes recipe:alternate-pure-iron-ingot

!recipes iron-rod
"""

buildings_help = """Print building details

!buildings

!buildings building:constructor
"""


class Optimization(commands.Cog):
    """Optimization commands"""

    @commands.command(pass_context=True, help=min_help)
    async def min(self, ctx, *args):
        await ctx.send(content=satisfaction.min(*args), file=discord.File("output.gv.png"))

    @commands.command(pass_context=True, help=max_help)
    async def max(self, ctx, *args):
        await ctx.send(content=satisfaction.max(*args), file=discord.File("output.gv.png"))

    @commands.command(pass_context=True, help=items_help)
    async def items(self, ctx, *args):
        await send_message(ctx, satisfaction.items(*args))

    @commands.command(pass_context=True, help=recipes_help)
    async def recipes(self, ctx, *args):
        await send_message(ctx, satisfaction.recipes(*args))

    @commands.command(pass_context=True, help=buildings_help)
    async def buildings(self, ctx, *args):
        await send_message(ctx, satisfaction.buildings(*args))


bot.add_cog(Optimization())

bot.run(token)

input("Enter")
