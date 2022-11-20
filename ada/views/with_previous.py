import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor


class WithPreviousView(discord.ui.View):
    def __init__(self, view: discord.ui.View, processor: Processor):
        super().__init__()
        self.__processor = processor
        if view:
            for item in view.children:
                self.add_item(item)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.primary, row=4)
    async def recipes_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        breadcrumbs.goto_prev_page()
        await self.__processor.do_and_edit(breadcrumbs, interaction)
