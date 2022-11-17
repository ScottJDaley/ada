import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor
from ada.views.with_previous import WithPreviousView


class RecipeView(discord.ui.View):
    def __init__(self, processor: Processor):
        super().__init__()
        self.__processor = processor

    @discord.ui.button(label="Building", style=discord.ButtonStyle.grey)
    async def recipes_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        recipe = self.__processor.lookup(breadcrumbs.primary_query())
        if not recipe:
            return

        building = recipe.crafter()
        query = f"{building.var()}"
        breadcrumbs.add_query(query)
        result = await self.__processor.do(query)
        message = result.messages(breadcrumbs)[0]
        message.view = WithPreviousView(message.view, self.__processor)
        await message.edit(interaction)
        self.stop()
