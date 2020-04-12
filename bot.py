import os
import discord
import asyncio
from dotenv import load_dotenv
from ada.ada import Ada
from ada.result import OptimizationResult
from ada.breadcrumbs import Breadcrumbs, BreadcrumbsException

CMD_PREFIX = 'ada '
REACTIONS_DONE = u'\u200B'  # zero-width space

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
client = discord.Client()
ada = Ada()


@client.event
async def on_ready():
    print('Connected to Discord as {0.user}'.format(client))

# TODO:
# item cards should show recipes
# item cards should allow reactions to select the recipe
# recipe cards should allow reactions to select the item


async def add_reactions(message, reactions):
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


def are_reactions_done(message):
    return len(message.embeds) == 0 or message.embeds[0].description.endswith(REACTIONS_DONE)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not message.content.startswith(CMD_PREFIX):
        return
    query = message.content[len(CMD_PREFIX):]
    result = await ada.do(query)
    result_message = result.message(Breadcrumbs.create(query))
    reply = await message.channel.send(content=result_message.content,
                                       embed=result_message.embed,
                                       file=result_message.file)
    await add_reactions(reply, result_message.reactions)


@client.event
async def on_raw_reaction_add(payload):
    user = await client.fetch_user(payload.user_id)
    if user == client.user:
        return
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    emoji = str(payload.emoji)

    if not are_reactions_done(message):
        def check(before, after):
            return (before.channel == channel and before.id == message.id
                    and are_reactions_done(after))
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

        result_message = result.message(breadcrumbs)
        await message.clear_reactions()
        await message.edit(content=result_message.content,
                           embed=result_message.embed)
        await add_reactions(message, result_message.reactions)
    except BreadcrumbsException as extraction_error:
        print(extraction_error)


client.run(token)
