import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor


class CrafterView(discord.ui.View):
    def __init__(self, processor: Processor):
        super().__init__()
        self.__processor = processor

    @discord.ui.button(label="Recipes", style=discord.ButtonStyle.grey)
    async def recipes_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"recipes for {breadcrumbs.current_page().query()}"
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__processor.do_and_edit(breadcrumbs, interaction)
        self.stop()