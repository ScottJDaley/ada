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
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    try:
        breadcrumbs = Breadcrumbs.extract(reaction.message.content)
        result = await ada.do(breadcrumbs.primary_query())
        query = result.handle_reaction(reaction.emoji, breadcrumbs)
        if query:
            result = await ada.do(query)

        result = result.message(breadcrumbs)
        await reaction.message.clear_reactions()
        await reaction.message.edit(content=result.content,
                                    embed=result.embed)
        for emoji in result.reactions:
            await reaction.message.add_reaction(emoji)
    except BreadcrumbsException as extraction_error:
        print(extraction_error)


client.run(token)
