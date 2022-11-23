from typing import cast

import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch
from ...query_parser import QueryParseException
from ...recipe_compare_query import RecipeCompareQuery


class CompareRecipesView(discord.ui.View):
    def __init__(self, include_alternates: bool, dispatch: Dispatch):
        super().__init__(timeout=None)
        self.__dispatch = dispatch
        self.__include_alternates = include_alternates

        self.__include_alternates_button = discord.ui.Button(
            label="Use Only Base Recipes For Stats" if include_alternates else "Allow Alternate Recipes For Stats",
            style=discord.ButtonStyle.secondary,
            custom_id="compare_recipes_alternates"
        )
        self.__include_alternates_button.callback = self.on_include_alternates
        self.add_item(self.__include_alternates_button)

    async def on_include_alternates(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__dispatch.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(RecipeCompareQuery, query)
        query.include_alternates = not query.include_alternates
        breadcrumbs.add_page(Breadcrumbs.Page(str(query), breadcrumbs.current_page().custom_ids()))
        await self.__dispatch.execute_and_replace(query, breadcrumbs, interaction)
