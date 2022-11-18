from typing import Callable

import discord

from ada.breadcrumbs import Breadcrumbs
from ada.db.entity import Entity
from ada.db.item import Item
from ada.processor import Processor


class OptimizationCategoryButton(discord.ui.Button):
    def __init__(
            self,
            label: str,
            custom_id: str,
            disabled: bool,
            processor: Processor
    ):
        super().__init__(style=discord.ButtonStyle.primary, label=label, disabled=disabled, custom_id=custom_id, row=0)
        self.__processor = processor

    async def callback(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_custom_id(self.custom_id)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)


class OptimizationCategoryView(discord.ui.View):
    def __init__(self, processor: Processor, active_category: str):
        super().__init__(timeout=None)
        self.__processor = processor
        self._add_categories(active_category, processor)

    def _add_categories(self, active_category: str, processor: Processor):
        for category in ["Inputs", "Outputs", "Recipes", "Buildings", "General"]:
            custom_id = category.lower()
            disabled = custom_id == active_category
            self.add_item(OptimizationCategoryButton(
                label=category,
                custom_id=custom_id,
                disabled=disabled,
                processor=processor
            ))


class EntityDropdown(discord.ui.Select):
    def __init__(self, entities: list[Entity], processor: Processor, callback: Callable[[str], None]):
        self.__processor = processor
        self.__callback = callback
        options = []
        for entity in entities:
            options.append(discord.SelectOption(label=entity.var(), description=entity.human_readable_name()))
        super().__init__(placeholder="Select an input", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selection_option = self.values[0]
        self.__callback(selection_option)


class InputsCategoryView(OptimizationCategoryView):
    def __init__(self, processor: Processor, inputs: dict[str, tuple[Item, float]]):
        super().__init__(processor, "inputs")
        self.__inputs = inputs
        entities = []
        for item, value in inputs.values():
            entities.append(item)
        self.add_item(EntityDropdown(entities, processor, self.on_select))

    def on_select(self, var: str):
        print("on_select", var)


class OutputsCategoryView(OptimizationCategoryView):
    def __init__(self, processor: Processor):
        super().__init__(processor, "outputs")


class RecipesCategoryView(OptimizationCategoryView):
    def __init__(self, processor: Processor):
        super().__init__(processor, "recipes")


class BuildingsCategoryView(OptimizationCategoryView):
    def __init__(self, processor: Processor):
        super().__init__(processor, "buildings")


class GeneralCategoryView(OptimizationCategoryView):
    def __init__(self, processor: Processor):
        super().__init__(processor, "general")
