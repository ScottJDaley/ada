import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor


class MultiEntityView(discord.ui.View):
    def __init__(self, processor: Processor):
        super().__init__()
        self.__processor = processor

    @discord.ui.button(label="Blah", style=discord.ButtonStyle.grey)
    async def recipes_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        # breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        # query = f"recipes for {breadcrumbs.primary_query()}"
        # breadcrumbs.add_query(query)
        # result = await self._processor.do(query)
        # message = result.messages(breadcrumbs)[0]
        # await message.edit(interaction)
        self.stop()
