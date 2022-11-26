from typing import List

import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch
from ...db.entity import Entity
from ...db.item import Item


# See https://github.com/Rapptz/discord.py/blob/master/examples/views/dropdown.py
class ProductDropdown(discord.ui.Select):
    def __init__(self, entities: List[Entity], dispatch: Dispatch):
        self.__dispatch = dispatch
        # print(f"Constructing EntityDropdown with start index {start_index}")
        options = self._get_options(entities)
        super().__init__(
            placeholder="Select one",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="product_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        selection_option = self.values[0]
        query = f"compare recipes for {selection_option}"
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)

    @staticmethod
    def _get_options(entities: List[Entity]) -> list[discord.SelectOption]:
        options = []
        for entity in entities:
            options.append(discord.SelectOption(label=entity.var(), description=entity.human_readable_name()))
        return options

    async def update_options(self, interaction: discord.Interaction, start: int):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        breadcrumbs.current_page().set_single_custom_id(str(start))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)


class CompareRecipeSelectorView(discord.ui.View):
    def __init__(self, entities: List[Item], dispatch: Dispatch):
        super().__init__(timeout=None)

        self.__dropdown = ProductDropdown(entities, dispatch)

        # Adds the dropdown to our view object.
        self.add_item(self.__dropdown)
