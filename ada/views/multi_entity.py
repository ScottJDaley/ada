import re
from typing import List, Optional, Union, Callable, Awaitable

import discord
from discord import ButtonStyle, Emoji, PartialEmoji

from ada.breadcrumbs import Breadcrumbs
from ada.db.entity import Entity
from ada.processor import Processor
from ada.views.with_previous import WithPreviousView


# See https://github.com/Rapptz/discord.py/blob/master/examples/views/dropdown.py
class EntityDropdown(discord.ui.Select):
    def __init__(self, entities: List[Entity], start_index: int, processor: Processor):
        self.__processor = processor
        print(f"Constructing EntityDropdown with start index {start_index}")
        options = self._get_options(entities, start_index)
        super().__init__(placeholder="Select one", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"{self.values[0]}"
        breadcrumbs.add_query(query)
        result = await self.__processor.do(query)
        message = result.messages(breadcrumbs)[0]
        message.view = WithPreviousView(message.view, self.__processor)
        await message.edit(interaction)

    @staticmethod
    def _get_options(entities: List[Entity], start: int) -> list[discord.SelectOption]:
        options = []
        end = len(entities)
        if end > 25:
            end = start + 25
        for i in range(start, end):
            entity = entities[i]
            options.append(discord.SelectOption(label=entity.var(), description=entity.human_readable_name()))
        return options

    async def update_options(self, interaction: discord.Interaction, start: int):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        breadcrumbs.set_start_index(start)
        query = f"{breadcrumbs.primary_query()}"
        result = await self.__processor.do(query)
        message = result.messages(breadcrumbs)[0]
        if breadcrumbs.has_prev_query():
            message.view = WithPreviousView(message.view, self.__processor)
        print("Message content:", message.content)
        await message.edit(interaction)


class ButtonWithCallback(discord.ui.Button):
    def __init__(
            self,
            *,
            style: ButtonStyle = ButtonStyle.secondary,
            label: Optional[str] = None,
            disabled: bool = False,
            custom_id: Optional[str] = None,
            url: Optional[str] = None,
            emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
            row: Optional[int] = None,
            callback: Callable[[discord.Interaction], Awaitable[None]],
    ):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.__callback = callback

    async def callback(self, interaction: discord.Interaction):
        await self.__callback(interaction)


class MultiEntityView(discord.ui.View):
    def __init__(self, entities: List[Entity], start_index: int, processor: Processor):
        super().__init__()

        self.__processor = processor
        self.__dropdown = EntityDropdown(entities, start_index, processor)

        num_entities = len(entities)

        self.__previous_button = ButtonWithCallback(
            label="Previous",
            style=discord.ButtonStyle.grey,
            emoji="⬅",
            disabled=start_index <= 0,
            callback=self._previous,
        )
        self.__num_button = discord.ui.Button(
            label=self._get_num_label(start_index, num_entities),
            style=discord.ButtonStyle.grey,
            disabled=True
        )
        self.__next_button = ButtonWithCallback(
            label="Next",
            style=discord.ButtonStyle.grey,
            emoji="➡",
            disabled=start_index > num_entities - 25,
            callback=self._next,
        )
        self.add_item(self.__previous_button)
        self.add_item(self.__num_button)
        self.add_item(self.__next_button)

        # Adds the dropdown to our view object.
        self.add_item(self.__dropdown)

    async def _previous(self, interaction: discord.Interaction):
        start_index = self._get_start_index()
        start_index -= 25
        if start_index <= 0:
            start_index = 0
        await self._update_buttons( interaction, start_index)

    async def _next(self, interaction: discord.Interaction):
        num_entities = self._get_num_entities()
        start_index = self._get_start_index()
        start_index += 25
        if start_index + 25 >= num_entities:
            start_index = num_entities - 25
        await self._update_buttons(interaction, start_index)

    async def _update_buttons(self, interaction: discord.Interaction, start_index):
        num_entities = self._get_num_entities()
        self.__previous_button.disabled = start_index <= 0
        self.__next_button.disabled = start_index > num_entities - 25
        self.__num_button.label = self._get_num_label(start_index, num_entities)
        await self.__dropdown.update_options(interaction, start_index)

    @staticmethod
    def _get_num_label(start_index: int, num_entities: int):
        start = start_index + 1
        end = start_index + 25
        return f"Showing {start} - {end} out of {num_entities} matches"

    def _get_num_entities(self):
        return int(re.findall(r'\d+', self.__num_button.label)[-1])

    def _get_start_index(self):
        return int(re.findall(r'\d+', self.__num_button.label)[0])
