from typing import List, Optional, Union, Callable, Awaitable

import discord
from discord import ButtonStyle, Emoji, PartialEmoji

from ada.breadcrumbs import Breadcrumbs
from ada.db.item import Item
from ada.processor import Processor
from ada.views.with_previous import WithPreviousView


# See https://github.com/Rapptz/discord.py/blob/master/examples/views/dropdown.py
class EntityDropdown(discord.ui.Select):
    def __init__(self, entities: List[Item], processor: Processor):
        self.__processor = processor
        self.__entities = entities
        options = self._get_options(0)
        super().__init__(placeholder="Select one", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = f"{self.values[0]}"
        breadcrumbs.add_query(query)
        result = await self.__processor.do(query)
        message = result.messages(breadcrumbs)[0]
        message.view = WithPreviousView(message.view, self.__processor)
        await message.edit(interaction)

    def _get_options(self, start: int) -> list[discord.SelectOption]:
        options = []
        end = len(self.__entities)
        if end > 25:
            end = start + 25
        for i in range(start, end):
            entity = self.__entities[i]
            options.append(discord.SelectOption(label=entity.var(), description=entity.human_readable_name()))
        return options

    def update_options(self, start: int):
        self.options = self._get_options(start)


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
    def __init__(self, entities: List[Item], processor: Processor):
        super().__init__()

        self.__num_entities = len(entities)
        self.__processor = processor
        self.__dropdown = EntityDropdown(entities, processor)

        if self.__num_entities > 25:
            self._add_navigation()

        # Adds the dropdown to our view object.
        self.add_item(self.__dropdown)

    def _add_navigation(self):
        self.__start_index = 0
        self.__previous_button = ButtonWithCallback(
            label="Previous",
            style=discord.ButtonStyle.grey,
            emoji="⬅",
            # emoji=":arrow_backward:",
            disabled=True,
            callback=self._previous,
        )
        self.__num_button = discord.ui.Button(
            label=self._get_num_label(),
            style=discord.ButtonStyle.grey,
            disabled=True
        )
        self.__next_button = ButtonWithCallback(
            label="Next",
            style=discord.ButtonStyle.grey,
            emoji="➡",
            # emoji=":arrow_forward:",
            disabled=False,
            callback=self._next,
        )
        self.add_item(self.__previous_button)
        self.add_item(self.__num_button)
        self.add_item(self.__next_button)

    async def _previous(self, interaction: discord.Interaction):
        self.__start_index -= 25
        if self.__start_index <= 0:
            self.__start_index = 0
        await self._update_buttons(interaction)

    async def _next(self, interaction: discord.Interaction):
        self.__start_index += 25
        if self.__start_index + 25 >= self.__num_entities:
            self.__start_index = self.__num_entities - 25
        await self._update_buttons(interaction)

    async def _update_buttons(self, interaction: discord.Interaction):
        self.__previous_button.disabled = self.__start_index <= 0
        self.__next_button.disabled = self.__start_index >= self.__num_entities - 25
        self.__num_button.label = self._get_num_label()
        self.__dropdown.update_options(self.__start_index)
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        view = self
        if breadcrumbs.has_prev_query():
            view = WithPreviousView(self, self.__processor)
        await interaction.response.edit_message(view=view)

    def _get_num_label(self):
        start = self.__start_index + 1
        end = self.__start_index + 25
        return f"Showing {start} - {end} out of {self.__num_entities} matches"
