import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch


class CrafterView(discord.ui.View):
    def __init__(self, dispatch: Dispatch):
        super().__init__(timeout=None)
        self.__dispatch = dispatch

    @discord.ui.button(label="Recipes", style=discord.ButtonStyle.grey, custom_id="crafter_recipes_for")
    async def recipes_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"recipes for {breadcrumbs.current_page().query()}"
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)
