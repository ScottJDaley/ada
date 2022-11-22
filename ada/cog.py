from typing import Optional

import discord.ext
from discord import app_commands
from discord.ext import commands

from .ada import Ada
from .ui.ada_dispatch import AdaDispatch


class AdaCog(commands.Cog):
    def __init__(self, bot: commands.Bot, ada_: Ada) -> None:
        self.__bot = bot
        self.__dispatch = AdaDispatch(ada_)

    @app_commands.command(name="help")
    async def help(self, interaction: discord.Interaction) -> None:
        """ /help """
        query = "help"
        await self.__dispatch.query_and_send(query, interaction)

    @app_commands.command(name="info", description="Information about items, buildings, and recipes.")
    @discord.app_commands.describe(entity="The item, building, or recipe you want information about.")
    async def info(self, interaction: discord.Interaction, entity: str) -> None:
        """ /info """
        query = entity
        await self.__dispatch.query_and_send(query, interaction)

    @app_commands.command(name="compare-recipes", description="Compare all recipes that produce an item.")
    @app_commands.describe(item='The item that is produced by the recipes')
    async def compare_recipes(self, interaction: discord.Interaction, item: str) -> None:
        """ /compare-recipes """
        query = f"compare recipes for {item}"
        await self.__dispatch.query_and_send(query, interaction)

    @app_commands.command(name="optimize", description="Compute an optimal production chain.")
    @app_commands.describe(
        output="Specify what you want to produce",
        input="Specify what the inputs are",
        include="Specify constraints for what should be included",
        exclude="Specify constraints for what should be excluded"
    )
    async def optimize(
            self, interaction: discord.Interaction, output: str, input: Optional[str],
            include: Optional[str], exclude: Optional[str]
    ) -> None:
        """ /compare-recipes """
        query = f"produce {output}"
        if input:
            query += f" from {input}"
        if include:
            query += f" with {include}"
        if exclude:
            query += f" excluding {exclude}"
        await self.__dispatch.query_and_send(query, interaction)
