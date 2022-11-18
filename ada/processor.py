from abc import ABC, abstractmethod

import discord

from ada.breadcrumbs import Breadcrumbs
from ada.result import Result


class Processor(ABC):
    @abstractmethod
    async def do(
        self, raw_query: str
    ) -> Result:
        pass

    @abstractmethod
    def lookup(self, var: str):
        pass

    async def do_and_edit(self, breadcrumbs: Breadcrumbs, interaction: discord.Interaction):
        result = await self.do(breadcrumbs.current_page().query())
        message = result.message(breadcrumbs)
        await message.edit(interaction)
