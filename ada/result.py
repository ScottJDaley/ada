from abc import ABC, abstractmethod

import discord
from discord import Embed
from discord.utils import MISSING

from ada.breadcrumbs import Breadcrumbs


class ResultMessage:
    def __init__(self) -> None:
        self.content = None
        self.embed = MISSING
        self.file = MISSING
        self.view = MISSING

    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content=self.content,
            embed=self.embed,
            file=self.file,
            view=self.view,
        )

    async def edit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=self.content,
            embed=self.embed,
            attachments=[self.file] if self.file else [],
            view=self.view,
        )


class Result(ABC):
    @abstractmethod
    def message(self, breadcrumbs: Breadcrumbs) -> ResultMessage:
        pass


class ErrorResult(Result):
    def __init__(self, msg: str) -> None:
        self.__msg = msg

    def __str__(self):
        return self.__msg

    def message(self, breadcrumbs: Breadcrumbs) -> ResultMessage:
        message = ResultMessage()
        message.embed = Embed(title="Error")
        message.embed.description = self.__msg
        message.content = str(breadcrumbs)
        return message
