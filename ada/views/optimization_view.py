import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor


class OptimizationView(discord.ui.View):
    def __init__(self, processor: Processor):
        super().__init__()
        self.__processor = processor

    @discord.ui.button(label="Inputs", style=discord.ButtonStyle.primary)
    async def inputs(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_start_index(0)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)
        self.stop()

    @discord.ui.button(label="Outputs", style=discord.ButtonStyle.primary)
    async def outputs(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_start_index(1)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)
        self.stop()

    @discord.ui.button(label="Recipes", style=discord.ButtonStyle.primary)
    async def recipes(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_start_index(2)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)
        self.stop()

    @discord.ui.button(label="Buildings", style=discord.ButtonStyle.primary)
    async def buildings(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_start_index(3)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)
        self.stop()

    @discord.ui.button(label="General", style=discord.ButtonStyle.primary)
    async def general(self, interaction: discord.Interaction, button: discord.ui.Button):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_start_index(4)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)
        self.stop()
