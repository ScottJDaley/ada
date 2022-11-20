from typing import Callable, Awaitable, cast

import discord

from ada.breadcrumbs import Breadcrumbs
from ada.db.entity import Entity
from ada.db.item import Item
from ada.optimization_query import Objective
from ada.optimization_result_data import OptimizationResultData
from ada.optimizer import OptimizationQuery
from ada.processor import Processor
from ada.query_parser import QueryParseException
from ada.views.with_previous import WithPreviousView


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
        print("Category button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        breadcrumbs.current_page().set_single_custom_id(self.custom_id)
        await self.__processor.do_and_edit(breadcrumbs, interaction)


class OptimizationCategoryView(discord.ui.View):
    def __init__(self, processor: Processor, active_category: str):
        super().__init__(timeout=None)
        self.__processor = processor
        self._add_categories(active_category, processor)

    def _add_categories(self, active_category: str, processor: Processor):
        print("Adding category buttons")
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
    def __init__(
            self,
            entities: list[Entity],
            processor: Processor,
            callback: Callable[[str, discord.Interaction], Awaitable[None]]):
        self.__processor = processor
        self.__callback = callback
        options = []
        for entity in entities:
            options.append(discord.SelectOption(label=entity.human_readable_name(), description=entity.var()))
        super().__init__(placeholder="Select one", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selection_option = self.values[0]
        selection_var = next(option.description for option in self.options if selection_option == option.label)
        await self.__callback(selection_var, interaction)


class OptimizationSelectorView(OptimizationCategoryView):
    def __init__(self, processor: Processor, data: OptimizationResultData, category: str):
        super().__init__(processor, category)
        self.__processor = processor
        self.__data = data
        entities: list[Entity] = []
        if category == "inputs":
            for item, _ in data.inputs().values():
                entities.append(item)
        elif category == "outputs":
            for item, _ in data.outputs().values():
                entities.append(item)
        elif category == "recipes":
            for recipe, _ in data.recipes().values():
                entities.append(recipe)
        elif category == "buildings":
            for crafter, _ in data.crafters().values():
                entities.append(crafter)
            for generator, _ in data.generators().values():
                entities.append(generator)
        # TODO: add cases for other categories
        self.add_item(EntityDropdown(entities, processor, self.on_select))

    @staticmethod
    def get_view(breadcrumbs: Breadcrumbs, processor: Processor, data: OptimizationResultData) -> discord.ui.View:
        # parts = custom_id.split(".")
        # category = parts[0] if len(parts) > 0 else ""
        # selected = "".join(parts)
        custom_ids = breadcrumbs.current_page().custom_ids()
        category = custom_ids[0]
        if len(breadcrumbs.current_page().custom_ids()) != 2:
            return OptimizationSelectorView(processor, data, category)
        selected = custom_ids[1]
        if category == "inputs":
            return InputCategoryView(processor, data, selected)
        if category == "outputs":
            return OutputsCategoryView(processor, data, selected)
        if category == "recipes":
            return RecipesCategoryView(processor, data, selected)
        # if category == "buildings":
        #     return BuildingsCategoryView(processor)
        # if category == "general":
        #     return GeneralCategoryView(processor)
        return OptimizationSelectorView(processor, data, category)

    async def on_select(self, selected: str, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        custom_ids = breadcrumbs.current_page().custom_ids()
        if len(custom_ids) < 2:
            breadcrumbs.current_page().add_custom_id(selected)
        else:
            custom_ids[1] = selected
        # We don't need to rerun the query here if we have the data.
        # Instead, just construct the correct view and update the breadcrumbs
        # TODO: check if self.__data is None and, if so, do a query instead
        view = OptimizationSelectorView.get_view(breadcrumbs, self.__processor, self.__data)
        if breadcrumbs.has_prev_page():
            view = WithPreviousView(view, self.__processor)
        await interaction.response.edit_message(content=str(breadcrumbs), view=view)


class InputCategoryView(OptimizationSelectorView):
    def __init__(self, processor: Processor, data: OptimizationResultData, selected: str):
        super().__init__(processor, data, "inputs")

        # discord.utils.get(self.children, custom_id="input_info")

        self.__processor = processor

        input, amount = data.inputs()[selected]

        self.__info_button = discord.ui.Button(
            label=input.human_readable_name(),
            style=discord.ButtonStyle.secondary,
            custom_id="input_info"
        )
        self.__info_button.callback = self.on_info
        self.add_item(self.__info_button)

        self.__amount_button = discord.ui.Button(
            label=str(amount),
            style=discord.ButtonStyle.secondary,
            custom_id="input_amount",
            disabled=True
        )
        self.add_item(self.__amount_button)

        self.__minimize_button = discord.ui.Button(
            label="Minimize",
            style=discord.ButtonStyle.success,
            custom_id="input_minimize"
        )
        self.__minimize_button.callback = self.on_minimize
        self.add_item(self.__minimize_button)

        self.__exclude_button = discord.ui.Button(
            label="Exclude",
            style=discord.ButtonStyle.danger,
            custom_id="input_exclude"
        )
        self.__exclude_button.callback = self.on_exclude
        self.add_item(self.__exclude_button)

    async def on_info(self, interaction: discord.Interaction):
        print("info button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.current_page().custom_ids()[-1]
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__processor.do_and_edit(breadcrumbs, interaction)

    async def on_minimize(self, interaction: discord.Interaction):
        print("minimize button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__processor.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        input_var = breadcrumbs.current_page().custom_ids()[-1]
        query.objective = Objective(input_var, False, -1)
        result = await self.__processor.execute(query)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        message = result.message(breadcrumbs)
        await message.edit(interaction)

    async def on_exclude(self, interaction: discord.Interaction):
        print("exclude button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__processor.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        input_var = breadcrumbs.current_page().custom_ids()[-1]
        query.add_input("item", input_var, 0, False)
        result = await self.__processor.execute(query)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        message = result.message(breadcrumbs)
        await message.edit(interaction)


class OutputsCategoryView(OptimizationSelectorView):
    def __init__(self, processor: Processor, data: OptimizationResultData, selected: str):
        super().__init__(processor, data, "outputs")

        self.__processor = processor

        output, amount = data.outputs()[selected]

        self.__info_button = discord.ui.Button(
            label=output.human_readable_name(),
            style=discord.ButtonStyle.secondary,
            custom_id="output_info"
        )
        self.__info_button.callback = self.on_info
        self.add_item(self.__info_button)

        self.__amount_button = discord.ui.Button(
            label=str(amount),
            style=discord.ButtonStyle.secondary,
            custom_id="output_amount",
            disabled=True
        )
        self.add_item(self.__amount_button)

        self.__maximize_button = discord.ui.Button(
            label="Maximize",
            style=discord.ButtonStyle.success,
            custom_id="output_maximize"
        )
        self.__maximize_button.callback = self.on_maximize
        self.add_item(self.__maximize_button)

        self.__exclude_button = discord.ui.Button(
            label="Exclude",
            style=discord.ButtonStyle.danger,
            custom_id="output_exclude",
            disabled=len(data.outputs()) <= 1
        )
        self.__exclude_button.callback = self.on_exclude
        self.add_item(self.__exclude_button)

    async def on_info(self, interaction: discord.Interaction):
        print("info button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.current_page().custom_ids()[-1]
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__processor.do_and_edit(breadcrumbs, interaction)

    async def on_maximize(self, interaction: discord.Interaction):
        print("maximize button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__processor.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        output_var = breadcrumbs.current_page().custom_ids()[-1]
        query.objective = Objective(output_var, True, 1)
        result = await self.__processor.execute(query)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        message = result.message(breadcrumbs)
        await message.edit(interaction)

    async def on_exclude(self, interaction: discord.Interaction):
        print("exclude button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__processor.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        output_var = breadcrumbs.current_page().custom_ids()[-1]
        query.add_output("item", output_var, 0, False)
        result = await self.__processor.execute(query)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        message = result.message(breadcrumbs)
        await message.edit(interaction)


class RecipesCategoryView(OptimizationSelectorView):
    def __init__(self, processor: Processor, data: OptimizationResultData, selected: str):
        super().__init__(processor, data, "recipes")

        self.__processor = processor

        recipe, amount = data.recipes()[selected]

        self.__info_button = discord.ui.Button(
            label=recipe.human_readable_name(),
            style=discord.ButtonStyle.secondary,
            custom_id="recipe_info"
        )
        self.__info_button.callback = self.on_info
        self.add_item(self.__info_button)

        self.__amount_button = discord.ui.Button(
            label=str(amount),
            style=discord.ButtonStyle.secondary,
            custom_id="recipe_amount",
            disabled=True
        )
        self.add_item(self.__amount_button)

        self.__exclude_button = discord.ui.Button(
            label="Exclude",
            style=discord.ButtonStyle.danger,
            custom_id="recipe_exclude"
        )
        self.__exclude_button.callback = self.on_exclude
        self.add_item(self.__exclude_button)

    async def on_info(self, interaction: discord.Interaction):
        print("info button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.current_page().custom_ids()[-1]
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__processor.do_and_edit(breadcrumbs, interaction)

    async def on_exclude(self, interaction: discord.Interaction):
        print("exclude button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__processor.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        recipe_var = breadcrumbs.current_page().custom_ids()[-1]
        query.add_exclude("recipe", recipe_var)
        result = await self.__processor.execute(query)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        message = result.message(breadcrumbs)
        await message.edit(interaction)


# class BuildingsCategoryView(OptimizationCategoryView):
#     def __init__(self, processor: Processor):
#         super().__init__(processor, "buildings")
#
#
# class GeneralCategoryView(OptimizationCategoryView):
#     def __init__(self, processor: Processor):
#         super().__init__(processor, "general")
