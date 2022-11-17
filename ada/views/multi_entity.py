from typing import List

import discord

from ada.breadcrumbs import Breadcrumbs
from ada.db.item import Item
from ada.processor import Processor
from ada.views.with_previous import WithPreviousView


# See https://github.com/Rapptz/discord.py/blob/master/examples/views/dropdown.py
class EntityDropdown(discord.ui.Select):
    def __init__(self, vars_: List[Item], processor: Processor):
        self.__processor = processor

        options = []
        for var in vars_:
            options.append(discord.SelectOption(label=var.human_readable_name(), description=var.var()))

        super().__init__(placeholder=f'Found {len(vars_)} matches', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"{self.values[0]}"
        breadcrumbs.add_query(query)
        result = await self.__processor.do(query)
        message = result.messages(breadcrumbs)[0]
        message.view = WithPreviousView(message.view, self.__processor)
        await message.edit(interaction)


class MultiEntityView(discord.ui.View):
    def __init__(self, vars_: List[Item], processor: Processor):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(EntityDropdown(vars_, processor))
