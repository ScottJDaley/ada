import discord.ext
from discord import app_commands
from discord.ext import commands

from .ada import Ada
from .ui.ada_dispatch import AdaDispatch


class AdaCog(commands.Cog):
    def __init__(self, bot: commands.Bot, ada_: Ada) -> None:
        self.__bot = bot
        self.__dispatch = AdaDispatch(ada_)

    @app_commands.command(name="ada")
    @discord.app_commands.describe(query="The query you wish to perform. Try /ada help to see examples.")
    async def help(self, interaction: discord.Interaction, query: str) -> None:
        """ /ada """
        await self.__dispatch.query_and_send(query, interaction)
