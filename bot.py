import os
import discord
import asyncio
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option #, create_choice
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component, create_select, create_select_option
from discord_slash.context import ComponentContext
from discord_slash.model import ButtonStyle
from dotenv import load_dotenv
from ada.ada import Ada
from ada.breadcrumbs import Breadcrumbs, BreadcrumbsException

load_dotenv()
CMD_PREFIX = os.getenv('DISCORD_PREFIX')
if not CMD_PREFIX:
    CMD_PREFIX = 'ada '

print(f"Discord Prefix: '{CMD_PREFIX}'")

REACTIONS_DONE = u'\u200B'  # zero-width space

guild_ids = None
restrict_slash_commands_to_guild = os.getenv('RESTRICT_SLASH_COMMANDS_TO_GUILD')
if restrict_slash_commands_to_guild:
    guild_ids = [int(restrict_slash_commands_to_guild)]
    print(f'Restricting slash commands to guild_id "{restrict_slash_commands_to_guild}"')
else:
    print(f'Setting up global slash commands.\nNOTE: For this to work, all servers with the bot must have the applications.commands scope.')

token = os.getenv('DISCORD_TOKEN')
client = discord.Client()
slash = SlashCommand(client, sync_commands=True)
ada = Ada()


@client.event
async def on_ready():
    print('Connected to Discord as {0.user}'.format(client))

# TODO:
# item cards should show recipes
# item cards should allow reactions to select the recipe
# recipe cards should allow reactions to select the item


@slash.slash(
    name="help",
    description="Help.",
    guild_ids=guild_ids,
)
async def help(ctx):
    query = "help"
    result = await ada.do(query)
    await _send_result(ctx, result, query)


@slash.slash(
    name="info",
    description="Information about items, buildings, and recipes.",
    guild_ids=guild_ids,
    options=
    [
        create_option(
            name="entity",
            description="The item, building, or recipe you want information about",
            option_type=3,
            required=True,
        ),
    ]
)
async def info(ctx, entity: str):
    query = f"{entity}"
    result = await ada.do(query)
    await _send_result(ctx, result, query)


@slash.slash(
    name="recipes",
    description="Look up the recipes that produce an item.",
    guild_ids=guild_ids,
    options=
    [
        create_option(
            name="item",
            description="The item that is produced by the recipes",
            option_type=3,
            required=True,
        ),
    ]
)
async def recipes(ctx, item: str):
    query = f"recipes for {item}"
    result = await ada.do(query)
    await _send_result(ctx, result, query)


@slash.slash(
    name="compare-recipes",
    description="Compare all recipes that produce an item.",
    guild_ids=guild_ids,
    options=
    [
        create_option(
            name="item",
            description="The item that is produced by the recipes",
            option_type=3,
            required=True,
        ),
    ]
)
async def compare_recipes(ctx, item: str):
    query = f"compare recipes for {item}"
    result = await ada.do(query)
    await _send_result(ctx, result, query)


@slash.slash(name="optimize",
             description="Compute an optimal production chain.",
             guild_ids=guild_ids,
             options=[
                 create_option(
                     name="output",
                     description="Specify what you want to produce",
                     option_type=3,
                     required=True,
                 ),
                 create_option(
                     name="input",
                     description="Specify what the inputs are",
                     option_type=3,
                     required=False,
                 ),
                 create_option(
                     name="include",
                     description="Specify constraints for what should be included",
                     option_type=3,
                     required=False,
                 ),
                 create_option(
                     name="exclude",
                     description="Specify constraints for what should be excluded",
                     option_type=3,
                     required=False,
                 ),
             ])
async def optimize(ctx, output: str, input: str = None, include: str = None, exclude: str = None):
    query = f"produce {output}"
    if input:
        query += f" from {input}"
    if include:
        query += f" with {include}"
    if exclude:
        query += f" excluding {exclude}"
    result = await ada.do(query)
    await _send_result(ctx, result, query)


# buttons = [
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Ore"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Plate"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
# ]

# buttons2 = [
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Ore"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Plate"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
# ]

# buttons3 = [
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Ore"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Plate"
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label="Iron Rod"
#     ),
# ]

# arrows = [
#     create_button(
#         style=ButtonStyle.grey,
#         emoji='◀️',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Page 1 of 14',
#         disabled=True,
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         emoji='▶️',
#     ),
# ]

# inside_buttons = [
#     create_button(
#         style=ButtonStyle.grey,
#         label='Back',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Recipes For',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Recipes From',
#     ),
# ]

# recipe_buttons = [
#     create_button(
#         style=ButtonStyle.grey,
#         label='Iron Ingot',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Iron Rod',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Constructor',
#     ),
# ]

# optimization_buttons = [
#     create_button(
#         style=ButtonStyle.grey,
#         label='Query',
#         disabled=True,
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Inputs',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Outputs',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Recipes',
#     ),
#     create_button(
#         style=ButtonStyle.grey,
#         label='Buildings',
#     ),
# ]


# select = create_select(
#     options=[# the options in your dropdown
#         create_select_option("Raw Query", value="query", emoji="🥼"),
#         create_select_option("Inputs", value="inputs", emoji="🧪"),
#         create_select_option("Outputs", value="outputs", emoji="🧫"),
#         create_select_option("Recipes", value="recipes", emoji="🧫"),
#         create_select_option("Buildings", value="buildings", emoji="🧫"),
#     ],
#     placeholder="See Details",  # the placeholder text to show when no options have been chosen
#     min_values=1,  # the minimum number of options a user must select
#     max_values=1,  # the maximum number of options a user can select
# )

# search_results = create_select(
#     options=[# the options in your dropdown
#         create_select_option("Iron Ore", value="iron-ore", emoji="🥼"),
#         create_select_option("Iron Rod", value="iron-rod", emoji="🧪"),
#         create_select_option("Iron Plate", value="iron-plate", emoji="🧫"),
#         create_select_option("Reinforced Iron Plate", value="reinforced-iron-plate", emoji="🧫"),
#         create_select_option("Iron wire", value="iron-wire", emoji="🧫"),
#         create_select_option("Load next 24 results...", value="next-results",),
#     ],
#     placeholder="Results",  # the placeholder text to show when no options have been chosen
#     min_values=1,  # the minimum number of options a user must select
#     max_values=1,  # the maximum number of options a user can select
# )

# action_row = create_actionrow(*buttons)
# action_row2 = create_actionrow(*buttons2)
# action_row3 = create_actionrow(*buttons3)
# arrow_row = create_actionrow(*arrows)
# inside_row = create_actionrow(*inside_buttons)
# recipe_row = create_actionrow(*recipe_buttons)
# optimization_row = create_actionrow(*optimization_buttons)

# @slash.slash(name="test-recipe", description="Test the bot!", guild_ids=guild_ids)
# async def _test_recipe(ctx):
#     query = f"recipe: iron rod"
#     result = await ada.do(query)
#     result_message = result.messages(Breadcrumbs.create(query))[0]
#     reply = await ctx.send(content=result_message.content,
#                     embed=result_message.embed,
#                     file=result_message.file,
#                     components=[recipe_row, arrow_row])

# @slash.slash(name="test-search", description="Test the bot!", guild_ids=guild_ids)
# async def _test_search(ctx):
#     await ctx.send("```iron.*```", components=[action_row, action_row2, action_row3, arrow_row])

# @slash.slash(name="test-search2", description="Test the bot!", guild_ids=guild_ids)
# async def _test_search2(ctx):
#     await ctx.send("```iron.*```", components=[create_actionrow(search_results)])

# @slash.slash(name="test-optimization", description="Test the bot!", guild_ids=guild_ids)
# async def _test_optimization(ctx):
#     query = f"produce 1 turbo motor"
#     result = await ada.do(query)
#     result_message = result.messages(Breadcrumbs.create(query))[0]
#     reply = await ctx.send(content=result_message.content,
#                     #embed=result_message.embed,
#                     file=result_message.file,
#                     components=[optimization_row, create_actionrow(select)])

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not message.content.startswith(CMD_PREFIX):
        return
    query = message.content[len(CMD_PREFIX):]
    result = await ada.do(query)
    for result_message in result.messages(Breadcrumbs.create(query)):
        reply = await message.channel.send(content=result_message.content,
                                           embed=result_message.embed,
                                           file=result_message.file)
        await _add_reactions(reply, result_message.reactions)


@client.event
async def on_raw_reaction_add(payload):
    user = await client.fetch_user(payload.user_id)
    if user == client.user:
        return
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author.id != client.user:
        return #Only respond to reactions on the bot's messages.
    emoji = str(payload.emoji)

    if not _are_reactions_done(message):
        def check(before, after):
            return (before.channel == channel and before.id == message.id
                    and _are_reactions_done(after))
        try:
            await client.wait_for('message_edit', check=check, timeout=20)
        except asyncio.TimeoutError:
            pass
    try:
        breadcrumbs = Breadcrumbs.extract(message.content)
        result = await ada.do(breadcrumbs.primary_query())
        query = result.handle_reaction(emoji, breadcrumbs)
        if query:
            result = await ada.do(query)

        result_message = result.messages(breadcrumbs)[0]
        await message.clear_reactions()
        await message.edit(content=result_message.content,
                           embed=result_message.embed)
        await _add_reactions(message, result_message.reactions)
    except BreadcrumbsException as extraction_error:
        print(extraction_error)

async def _add_reactions(message, reactions):
    for reaction in reactions:
        await message.add_reaction(reaction)
    content = message.content
    if len(message.embeds) == 0:
        return
    embed = message.embeds[0]
    if not embed.description:
        embed.description = REACTIONS_DONE
    else:
        embed.description = embed.description + REACTIONS_DONE
    await message.edit(content=content, embed=embed)


def _are_reactions_done(message):
    return len(message.embeds) == 0 or message.embeds[0].description.endswith(REACTIONS_DONE)

async def _send_result(ctx, result, query):
    for result_message in result.messages(Breadcrumbs.create(query)):
        reply = await ctx.send(content=result_message.content,
                       embed=result_message.embed,
                       file=result_message.file)
        await _add_reactions(reply, result_message.reactions)


client.run(token)
