from abc import ABC, abstractmethod
from typing import Optional

import discord

from .breadcrumbs import Breadcrumbs
from ..db.entity import Entity
from ..query import Query
from ..result import Result


class Dispatch(ABC):
    # Processes the raw query and returns the result
    @abstractmethod
    async def query(self, raw_query: str) -> Result:
        pass

    # Parses the raw query
    @abstractmethod
    def parse(self, raw_query: str) -> Query:
        pass

    # Executes a parsed query and returns the result
    @abstractmethod
    async def execute(self, query: Query) -> Result:
        pass

    # Looks up an entity by variable name
    @abstractmethod
    def lookup(self, var: str) -> Entity:
        pass

    # Sends the result as a new message to the interaction
    @abstractmethod
    async def send(self, result: Result, breadcrumbs: Breadcrumbs, interaction: discord.Interaction):
        pass

    # Replaces the interaction message with the result
    @abstractmethod
    async def replace(self, result: Result, breadcrumbs: Breadcrumbs, interaction: discord.Interaction):
        pass

    # Processes the raw query and sends a new message for the interaction
    async def query_and_send(self, raw_query: str, interaction: discord.Interaction):
        result = await self.query(raw_query)
        breadcrumbs = Breadcrumbs.create(raw_query)
        await self.send(result, breadcrumbs, interaction)

    # Executes a parsed query and sends a new message for the interaction
    async def execute_and_send(self, query: Query, interaction: discord.Interaction):
        result = await self.execute(query)
        breadcrumbs = Breadcrumbs.create(str(query))
        await self.send(result, breadcrumbs, interaction)

    # Processes the query in the breadcrumbs and replaces the interaction message
    async def query_and_replace(self, breadcrumbs: Breadcrumbs, interaction: discord.Interaction):
        raw_query = breadcrumbs.current_page().query()
        result = await self.query(raw_query)
        await self.replace(result, breadcrumbs, interaction)

    # Executes a parsed query and replaces the interaction message
    async def execute_and_replace(
            self,
            query: Query,
            breadcrumbs: Breadcrumbs,
            interaction: discord.Interaction
    ):
        result = await self.execute(query)
        await self.replace(result, breadcrumbs, interaction)

    # Edits the fields of the interaction message
    @staticmethod
    async def edit(
            breadcrumbs: Breadcrumbs,
            interaction: discord.Interaction,
            embed: Optional[discord.Embed] = discord.utils.MISSING,
            file: Optional[discord.File] = discord.utils.MISSING,
            view: Optional[discord.ui.View] = discord.utils.MISSING
    ):
        await interaction.response.edit_message(
            content=str(breadcrumbs),
            embed=embed,
            attachments=[file] if file else discord.utils.MISSING,
            view=view,
        )
