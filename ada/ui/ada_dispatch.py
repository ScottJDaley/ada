import discord

from .breadcrumbs import Breadcrumbs
from .dispatch import Dispatch
from .result_message_factory import ResultMessageFactory
from ..ada import Ada
from ..db.entity import Entity
from ..query import Query
from ..result import Result


class AdaDispatch(Dispatch):
    def __init__(self, ada: Ada):
        self.__ada = ada

    async def query(self, raw_query: str) -> Result:
        return await self.__ada.query(raw_query)

    def parse(self, raw_query: str) -> Query:
        return self.__ada.parse(raw_query)

    async def execute(self, query: Query) -> Result:
        return await self.__ada.execute(query)

    def lookup(self, var: str) -> Entity:
        return self.__ada.lookup(var)

    # Sends the result as a new message to the interaction
    async def send(self, result: Result, breadcrumbs: Breadcrumbs, interaction: discord.Interaction):
        message = ResultMessageFactory.from_result(result, breadcrumbs, self)
        await message.send(interaction)

    # Replaces the interaction message with the result
    async def replace(self, result: Result, breadcrumbs: Breadcrumbs, interaction: discord.Interaction):
        message = ResultMessageFactory.from_result(result, breadcrumbs, self)
        await message.replace(interaction)
