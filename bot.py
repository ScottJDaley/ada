import os
import discord
from dotenv import load_dotenv
from ada.ada import Ada
from ada.result import OptimizationResult
from ada.breadcrumbs import Breadcrumbs, BreadcrumbsException

CMD_PREFIX = 'ada '

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
client = discord.Client()
ada = Ada()


@client.event
async def on_ready():
    print('Connected to Discord as {0.user}'.format(client))

# info query lists should be paginated with 9 per page.
# lists should allow reactions to select th item
# item cards should show recipes
# item cards should allow reactions to select the recipe
# recipe cards should allow reactions to select the item


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(CMD_PREFIX):
        query = message.content[len(CMD_PREFIX):]
        result = await ada.do(query)
        result_message = result.message(Breadcrumbs.create(query))
        reply = await message.channel.send(content=result_message.content,
                                           embed=result_message.embed,
                                           file=result_message.file)
        for reaction in result_message.reactions:
            await reply.add_reaction(reaction)


@client.event
async def on_raw_reaction_add(payload):
    user = await client.fetch_user(payload.user_id)
    if user == client.user:
        return
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    emoji = payload.emoji.name
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
        for emoji in result_message.reactions:
            await message.add_reaction(emoji)
    except BreadcrumbsException as extraction_error:
        print(extraction_error)


client.run(token)
