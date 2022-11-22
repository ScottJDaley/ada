from __future__ import annotations

from typing import Optional

import discord

from .breadcrumbs import Breadcrumbs


class ResultMessage:
    def __init__(self, breadcrumbs: Breadcrumbs) -> None:
        self.breadcrumbs: Breadcrumbs = breadcrumbs
        self.content: Optional[str] = None
        self.embed: discord.Embed = discord.utils.MISSING
        self.file: discord.File = discord.utils.MISSING
        self.view: discord.ui.View = discord.utils.MISSING

    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content=self.breadcrumbs.format_content(self.content),
            embed=self.embed if self.embed else discord.utils.MISSING,
            file=self.file if self.file else discord.utils.MISSING,
            view=self.view if self.view else discord.utils.MISSING,
        )

    async def replace(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=self.breadcrumbs.format_content(self.content),
            embed=self.embed,
            attachments=[self.file] if self.file else [],
            view=self.view,
        )
