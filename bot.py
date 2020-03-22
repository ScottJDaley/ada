from dotenv import load_dotenv
from discord.ext import commands
from satisfaction import Satisfaction
import os
import discord
import math
import traceback
import re
import query_parser


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

satisfaction = Satisfaction()

CMD_PREFIX = '!'

bot = commands.Bot(command_prefix=CMD_PREFIX)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


# @bot.event
# async def on_error(event, *args, **kwargs):
#     print('Ignoring exception in command {}:'.format(
#         ctx.command), file=sys.stderr)
#     traceback.print_exception(
#         type(error), error, error.__traceback__, file=sys.stderr)

# @bot.event
# async def on_error(event, *args, **kwargs):
#     message = args[0]  # Gets the message object
#     traceback.print_exception()  # logs the error
#     await bot.send_message(message.channel, "You caused an error!")


# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.errors.CheckFailure):
#         await ctx.send('You do not have the correct role for this command.')
#     if not isinstance(error, commands.CheckFailure):
#         await ctx.message.add_reaction(':false:508021839981707304')
#         await ctx.send("<a:siren:507952050181636098> `Invalid command` <a:siren:507952050181636098>")


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
 - If the {objective} is omitted, the weighted-resources objective is used by default.
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


async def send_message(ctx, msg, file=None):
    DISCORD_MESSAGE_LIMIT = 2000
    while len(msg) > DISCORD_MESSAGE_LIMIT:
        newline_index = msg.rfind('\n', 0, DISCORD_MESSAGE_LIMIT)
        await ctx.send(msg[:newline_index])
        msg = msg[newline_index:]
    await ctx.send(content=msg, file=file)


async def send_item_embed(ctx, item):
    await ctx.send(content='`' + CMD_PREFIX + 'items ' + item.var() + '`', embed=item.embed())

ITEMS_PER_PAGE = 9

NUM_EMOJI = ['0️⃣', '1️⃣', '2️⃣', '3️⃣',
             '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']


# async def add_num_reactions(message, num):
#     for i in range(1, num+1):
#         await message.add_reaction(NUM_EMOJI[i])


def first_index(page):
    return (page - 1) * ITEMS_PER_PAGE


def last_index(page, items):
    return min(first_index(page) + ITEMS_PER_PAGE, len(items))


def count_on_page(page, items):
    return min(ITEMS_PER_PAGE, len(items) - first_index(page))


def num_pages(items):
    return math.ceil(len(items) / ITEMS_PER_PAGE)


def create_items_embed(items, page):
    embed = discord.Embed()

    embed.set_footer(text="Page " + str(page) + " of " + str(num_pages(items)))

    for index in range(first_index(page), last_index(page, items)):
        item = items[index]
        embed.add_field(name='`' + item.var() + '`',
                        value=item.human_readable_name(), inline=False)
    return embed


@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return
    message = reaction.message
    if not message.content.startswith('`') or not message.content.endswith('`'):
        return
    content = message.content[1:-1]
    if not content.startswith(CMD_PREFIX):
        return
    args = content.split(' ')
    command = args[0][1:]
    if command != 'items':
        return

    if reaction.emoji != '◀️' and reaction.emoji != '▶️' and reaction.emoji != '↗️':
        return

    match = re.match("Page ([0-9]+) of ([0-9]+)",
                     message.embeds[0].footer.text)
    current_page = int(match.group(1))
    num_pages = int(match.group(2))

    def check(message):
        return True

    async def request_input(msg):
        await message.channel.send(content=msg)
        input_message = await bot.wait_for('message', check=check)
        return input_message.content

    result = await satisfaction.items(request_input, *args[1:])
    items = result.items

    if reaction.emoji == '↗️':
        choices = [item.var() for item in items[first_index(
            current_page):last_index(current_page, items)]]
        choice = await query_parser.make_choice(
            "Which item would you like more information about?",
            request_input, choices)
        item_var = choices[choice]
        for item in items:
            if item.var() == item_var:
                chosen_item = item
                break
        await send_item_embed(message.channel, chosen_item)
        return

    if reaction.emoji == '◀️':
        if current_page <= 1:
            return
        page = current_page - 1
    elif reaction.emoji == '▶️':
        if current_page >= num_pages:
            return
        page = current_page + 1

    await message.clear_reactions()
    await message.edit(embed=create_items_embed(items, page))

    if page > 1:
        await message.add_reaction('◀️')
    await message.add_reaction('↗️')
    if page < num_pages:
        await message.add_reaction('▶️')


class Information(commands.Cog):
    """Informational commands"""

    def __init__(self, bot):
        self.__bot = bot

    async def handle_items_cmd(self, ctx, page, *args):
        def check(msg):
            return True

        async def request_input(msg):
            await send_message(ctx, msg)
            input_message = await self.__bot.wait_for('message', check=check)
            return input_message.content

        result = await satisfaction.items(request_input, *args)
        items = result.items
        if len(items) == 1:
            await send_item_embed(ctx, items[0])
            return

        embed = create_items_embed(items, page)
        content = '`' + CMD_PREFIX + 'items ' + result.normalized_args + '`'
        msg = await ctx.send(content=content, embed=embed)

        if page > 1:
            await msg.add_reaction('◀️')
        await msg.add_reaction('↗️')
        if page < num_pages(items):
            await msg.add_reaction('▶️')

    @commands.command(pass_context=True, help=items_help)
    async def items(self, ctx, *args):
        await self.handle_items_cmd(ctx, 1, *args)

    @commands.command(pass_context=True, help=recipes_help)
    async def recipes(self, ctx, *args):
        await send_message(ctx, satisfaction.recipes(*args))

    @commands.command(pass_context=True, help=buildings_help)
    async def buildings(self, ctx, *args):
        await send_message(ctx, satisfaction.buildings(*args))

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))


class Optimization(commands.Cog):
    """Optimization commands"""

    def __init__(self, bot):
        self.__bot = bot

    @commands.command(pass_context=True, help=min_help)
    async def min(self, ctx, *args):
        def check(msg):
            return True

        async def request_input(msg):
            await send_message(ctx, msg)
            input_message = await self.__bot.wait_for('message', check=check)
            return input_message.content
        result = await satisfaction.min(request_input, *args)
        file = None
        if result.has_solution():
            filename = 'output.gv'
            result.generate_graph_viz(filename)
            file = discord.File(filename + '.png')
        await send_message(ctx, str(result), file)

    @commands.command(pass_context=True, help=max_help)
    async def max(self, ctx, *args):
        def check(msg):
            return True

        async def request_input(msg):
            await send_message(ctx, msg)
            input_message = await self.__bot.wait_for('message', check=check)
            return input_message.content
        result = await satisfaction.max(request_input, *args)
        file = None
        if result.has_solution():
            filename = 'output.gv'
            result.generate_graph_viz(filename)
            file = discord.File(filename + '.png')
        await send_message(ctx, str(result), file)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))


bot.add_cog(Information(bot))
bot.add_cog(Optimization(bot))

bot.run(token)
