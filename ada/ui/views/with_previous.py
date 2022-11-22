import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch


class WithPreviousView(discord.ui.View):
    def __init__(self, view: discord.ui.View, dispatch: Dispatch):
        super().__init__()
        self.__dispatch = dispatch
        if view:
            for item in view.children:
                self.add_item(item)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.primary, row=4)
    async def recipes_for(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        breadcrumbs.goto_prev_page()
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)
