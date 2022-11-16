from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ada.ada import Ada
from ada.breadcrumbs import Breadcrumbs


class Cog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ada = Ada()

    @app_commands.command(name="help")
    async def help(self, interaction: discord.Interaction) -> None:
        """ /help """
        query = "help"
        await self.query_and_respond(query, interaction)

    @app_commands.command(name="info", description="Information about items, buildings, and recipes.")
    @app_commands.describe(entity="The item, building, or recipe you want information about.")
    async def info(self, interaction: discord.Interaction, entity: str) -> None:
        """ /info """
        query = entity
        await self.query_and_respond(query, interaction)

    @app_commands.command(name="compare-recipes", description="Compare all recipes that produce an item.")
    @app_commands.describe(item='The item that is produced by the recipes')
    async def compare_recipes(self, interaction: discord.Interaction, item: str) -> None:
        """ /compare-recipes """
        query = f"compare recipes for {item}"
        await self.query_and_respond(query, interaction)

    @app_commands.command(name="optimize", description="Compute an optimal production chain.")
    @app_commands.describe(output="Specify what you want to produce",
                           input="Specify what the inputs are",
                           include="Specify constraints for what should be included",
                           exclude="Specify constraints for what should be excluded")
    async def optimize(self, interaction: discord.Interaction, output: str, input: Optional[str],
                       include: Optional[str], exclude: Optional[str]) -> None:
        """ /compare-recipes """
        query = f"produce {output}"
        if input:
            query += f" from {input}"
        if include:
            query += f" with {include}"
        if exclude:
            query += f" excluding {exclude}"
        await self.query_and_respond(query, interaction)

    async def query_and_respond(self, query: str, interaction: discord.Interaction):
        result = await self.ada.do(query)
        message = result.messages(Breadcrumbs.create(query))[0]
        await interaction.response.send_message(
            content=message.content,
            embed=message.embed,
            file=message.file,
            ephemeral=True
        )
