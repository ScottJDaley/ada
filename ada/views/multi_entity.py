from typing import List

import discord

from ada.breadcrumbs import Breadcrumbs
from ada.db.item import Item
from ada.processor import Processor
from ada.views.with_previous import WithPreviousView


# Defines a custom Select containing colour options
# that the user can choose. The callback function
# of this class is called when the user changes their choice
class EntityDropdown(discord.ui.Select):
    def __init__(self, vars_: List[Item], processor: Processor):
        self.__processor = processor
        # Set the options that will be presented inside the dropdown
        options = []
        for var in vars_:
            options.append(discord.SelectOption(label=var.human_readable_name(), description=var.var()))

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder=f'Found {len(vars_)} matches.', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        # await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')

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
