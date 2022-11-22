import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch


class ItemView(discord.ui.View):
    def __init__(self, dispatch: Dispatch):
        super().__init__()
        self.__dispatch = dispatch

    @discord.ui.button(label="Browse Recipes", style=discord.ButtonStyle.secondary, custom_id="item_browse_recipes")
    async def browse_recipes(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"recipes for {breadcrumbs.current_page().query()}"
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)

    @discord.ui.button(label="Compare Recipes", style=discord.ButtonStyle.secondary, custom_id="item_compare_recipes")
    async def compare_recipes(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"compare recipes for {breadcrumbs.current_page().query()}"
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)
