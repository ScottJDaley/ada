import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor


class RecipeView(discord.ui.View):
    def __init__(self, processor: Processor):
        super().__init__()
        self.__processor = processor

    @discord.ui.button(label="Building", style=discord.ButtonStyle.grey)
    async def recipes_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        recipe = self.__processor.lookup(breadcrumbs.current_page().query())
        if not recipe:
            return

        building = recipe.crafter()
        query = building.var()
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__processor.do_and_edit(breadcrumbs, interaction)
