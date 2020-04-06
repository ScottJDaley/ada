import os
import discord
from dotenv import load_dotenv
from ada import Ada
from result import OptimizationResult


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

CMD_PREFIX = 'ada '

client = discord.Client()

ada = Ada()


@client.event
async def on_ready():
    print('Connected to Discord as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(CMD_PREFIX):
        query = message.content[len(CMD_PREFIX):]
        result = await ada.do(query)
        print(result)
        file = None
        embed = result.embed()
        if isinstance(result, OptimizationResult):
            filename = 'output.gv'
            result.generate_graph_viz(filename)
            file = discord.File(filename + '.png')
            embed.set_image(url="attachment://" + filename + ".png")
        await message.channel.send(content=str(result),
                                   embed=embed,
                                   file=file)

client.run(token)
