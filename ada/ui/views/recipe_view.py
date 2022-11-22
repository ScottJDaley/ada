from typing import cast

import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch
from ...db.recipe import Recipe


class RecipeView(discord.ui.View):
    def __init__(self, dispatch: Dispatch):
        super().__init__()
        self.__dispatch = dispatch

    @discord.ui.button(label="Building", style=discord.ButtonStyle.grey)
    async def recipes_for(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        recipe = self.__dispatch.lookup(breadcrumbs.current_page().query())
        if not recipe:
            return
        recipe = cast(Recipe, recipe)
        building = recipe.crafter()
        query = building.var()
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)
