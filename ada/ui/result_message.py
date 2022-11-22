from __future__ import annotations

import discord

from .breadcrumbs import Breadcrumbs


class ResultMessage:
    def __init__(self, breadcrumbs: Breadcrumbs) -> None:
        self.breadcrumbs: Breadcrumbs = breadcrumbs
        self.embed: discord.Embed = discord.utils.MISSING
        self.file: discord.File = discord.utils.MISSING
        self.view: discord.ui.View = discord.utils.MISSING

    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content=str(self.breadcrumbs),
            embed=self.embed,
            file=self.file,
            view=self.view,
        )

    async def replace(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=str(self.breadcrumbs),
            embed=self.embed,
            attachments=[self.file] if self.file else [],
            view=self.view,
        )
