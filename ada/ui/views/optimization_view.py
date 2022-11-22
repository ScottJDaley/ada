from functools import partial
from typing import Awaitable, Callable, cast

import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch
from ...db.entity import Entity
from ...optimization_query import Objective, OptimizationQuery
from ...optimization_result_data import OptimizationResultData
from ...query_parser import QueryParseException


# TODO: Finish up persistence work here:
# class OptimizationContainer:
#     def __init__(
#             self,
#             processor: Processor,
#             data: Optional[OptimizationResultData] = None,
#             query: Optional[OptimizationQuery] = None):
#         self.__processor = processor
#         self.__data = data
#         self.__query = query
#
#     def _restore_query(self, breadcrumbs: Breadcrumbs):
#         raw_query = breadcrumbs.current_page().query()
#         query = self.__processor.parse(raw_query)
#         self.__query = cast(OptimizationQuery, query)
#
#     def query(self, breadcrumbs: Breadcrumbs) -> OptimizationQuery:
#         if not self.__query:
#             self._restore_query(breadcrumbs)
#         return self.__query
#
#     def _restore_data(self, breadcrumbs: Breadcrumbs):
#         if not self.__query:
#             self._restore_query(breadcrumbs)
#         result = await self.__processor.execute(self.__query)
#         # TODO: need to get OptimizationResultData here, but only if we cast to an OptimizationResult which
#         # results in a circular dependency


# Note:         # discord.utils.get(self.children, custom_id="input_info")

class OptimizationCategoryView(discord.ui.View):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery,
            active_category: str
    ):
        super().__init__(timeout=None)
        self.__dispatch = dispatch
        self.__data = data
        self.__query = query
        self._add_categories(active_category)

    def _add_categories(self, active_category: str):
        print("Adding category buttons")
        for category in ["Inputs", "Outputs", "Recipes", "Buildings", "Settings"]:
            custom_id = category.lower()
            disabled = custom_id == active_category
            button = discord.ui.Button(
                label=category,
                style=discord.ButtonStyle.primary,
                custom_id=custom_id,
                disabled=disabled,
                row=0,
            )
            button.callback = partial(self.on_category, custom_id)
            self.add_item(button)

    async def on_category(self, custom_id: str, interaction: discord.Interaction):
        print("Category button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        breadcrumbs.current_page().clear_custom_ids()
        breadcrumbs.current_page().add_custom_id(custom_id)
        # We don't need to rerun the query here if we have the data.
        # Instead, just construct the correct view and update the breadcrumbs
        # TODO: check if self.__data is None and, if so, do a query instead
        view = OptimizationSelectorView.get_view(breadcrumbs, self.__dispatch, self.__data, self.__query)
        await self.__dispatch.edit(breadcrumbs=breadcrumbs, interaction=interaction, view=view)


class EntityDropdown(discord.ui.Select):
    def __init__(
            self,
            entities: list[Entity],
            dispatch: Dispatch,
            callback: Callable[[str, discord.Interaction], Awaitable[None]]
    ):
        self.__dispatch = dispatch
        self.__callback = callback
        options = []
        for entity in entities:
            options.append(discord.SelectOption(label=entity.human_readable_name(), description=entity.var()))
        super().__init__(
            placeholder="Select one",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="optimization_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        selection_option = self.values[0]
        selection_var = next(option.description for option in self.options if selection_option == option.label)
        await self.__callback(selection_var, interaction)


class OptimizationSelectorView(OptimizationCategoryView):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery,
            category: str
    ):
        super().__init__(dispatch, data, query, category)
        self.__dispatch = dispatch
        self.__data = data
        self.__query = query
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
        self.add_item(EntityDropdown(entities, dispatch, self.on_select))

    @staticmethod
    def get_view(
            breadcrumbs: Breadcrumbs, dispatch: Dispatch, data: OptimizationResultData,
            query: OptimizationQuery
    ) -> discord.ui.View:
        dispatch = dispatch
        custom_ids = breadcrumbs.current_page().custom_ids()
        category = custom_ids[0]
        if category == "settings":
            return SettingsCategoryView(dispatch, data, query)
        if len(breadcrumbs.current_page().custom_ids()) != 2:
            return OptimizationSelectorView(dispatch, data, query, category)
        selected = custom_ids[1]
        if category == "inputs":
            return InputCategoryView(dispatch, data, query, selected)
        if category == "outputs":
            return OutputsCategoryView(dispatch, data, query, selected)
        if category == "recipes":
            return RecipesCategoryView(dispatch, data, query, selected)
        if category == "buildings":
            return BuildingsCategoryView(dispatch, data, query, selected)
        return OptimizationSelectorView(dispatch, data, query, category)

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
        view = OptimizationSelectorView.get_view(breadcrumbs, self.__dispatch, self.__data, self.__query)
        await self.__dispatch.edit(breadcrumbs=breadcrumbs, interaction=interaction, view=view)


class InfoButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str, dispatch: Dispatch):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=custom_id)
        self.__dispatch = dispatch

    async def callback(self, interaction: discord.Interaction) -> None:
        print("info button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.current_page().custom_ids()[-1]
        breadcrumbs.add_page(Breadcrumbs.Page(query))
        await self.__dispatch.query_and_replace(breadcrumbs, interaction)


class EditQueryButton(discord.ui.Button):
    def __init__(self, custom_id: str, edit_query: Callable[[OptimizationQuery, str], None], dispatch: Dispatch):
        super().__init__(label="Exclude", style=discord.ButtonStyle.danger, custom_id=custom_id)
        self.__dispatch = dispatch
        self.__edit_query = edit_query

    async def callback(self, interaction: discord.Interaction) -> None:
        print("edit query button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__dispatch.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        input_var = breadcrumbs.current_page().custom_ids()[-1]
        self.__edit_query(query, input_var)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query), [breadcrumbs.current_page().custom_ids()[0]]))
        await self.__dispatch.execute_and_replace(query, breadcrumbs, interaction)


class InputCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery,
            selected: str
    ):
        super().__init__(dispatch, data, query, "inputs")

        self.__dispatch = dispatch

        input, amount = data.inputs()[selected]

        self.add_item(InfoButton(label=input.human_readable_name(), custom_id="input_info", dispatch=dispatch))

        self.add_item(
            discord.ui.Button(
                label=str(amount),
                style=discord.ButtonStyle.secondary,
                custom_id="input_amount",
                disabled=True
            )
        )

        self.__minimize_button = discord.ui.Button(
            label="Minimize",
            style=discord.ButtonStyle.success,
            custom_id="input_minimize"
        )
        self.__minimize_button.callback = self.on_minimize
        self.add_item(self.__minimize_button)

        self.add_item(
            EditQueryButton(
                custom_id="input_exclude",
                edit_query=(lambda q, var: q.add_input(var, 0, False)),
                dispatch=self.__dispatch
            )
        )

    async def on_minimize(self, interaction: discord.Interaction):
        print("minimize button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__dispatch.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        input_var = breadcrumbs.current_page().custom_ids()[-1]
        query.objective = Objective(input_var, False, -1)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        await self.__dispatch.execute_and_replace(query, breadcrumbs, interaction)


class OutputsCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery,
            selected: str
    ):
        super().__init__(dispatch, data, query, "outputs")

        self.__dispatch = dispatch

        output, amount = data.outputs()[selected]

        self.add_item(InfoButton(label=output.human_readable_name(), custom_id="output_info", dispatch=dispatch))

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

        self.add_item(
            EditQueryButton(
                custom_id="output_exclude",
                edit_query=(lambda q, var: q.add_output(var, 0, False)),
                dispatch=self.__dispatch
            )
        )

    async def on_maximize(self, interaction: discord.Interaction):
        print("maximize button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__dispatch.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        output_var = breadcrumbs.current_page().custom_ids()[-1]
        query.objective = Objective(output_var, True, 1)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        await self.__dispatch.execute_and_replace(query, breadcrumbs, interaction)


class RecipesCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery,
            selected: str
    ):
        super().__init__(dispatch, data, query, "recipes")

        self.__dispatch = dispatch

        recipe, amount = data.recipes()[selected]

        self.add_item(InfoButton(label=recipe.human_readable_name(), custom_id="recipe_info", dispatch=dispatch))

        self.__amount_button = discord.ui.Button(
            label=str(amount),
            style=discord.ButtonStyle.secondary,
            custom_id="recipe_amount",
            disabled=True
        )
        self.add_item(self.__amount_button)

        self.add_item(
            EditQueryButton(
                custom_id="recipe_exclude",
                edit_query=(lambda q, var: q.add_exclude(var)),
                dispatch=self.__dispatch
            )
        )


class BuildingsCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery,
            selected: str
    ):
        super().__init__(dispatch, data, query, "buildings")

        self.__dispatch = dispatch

        if selected in data.crafters():
            building, amount = data.crafters()[selected]
        else:
            building, amount = data.generators()[selected]

        self.add_item(InfoButton(label=building.human_readable_name(), custom_id="building_info", dispatch=dispatch))

        self.__amount_button = discord.ui.Button(
            label=str(amount),
            style=discord.ButtonStyle.secondary,
            custom_id="building_amount",
            disabled=True
        )
        self.add_item(self.__amount_button)

        self.add_item(
            EditQueryButton(
                custom_id="building_exclude",
                edit_query=(lambda q, var: q.add_exclude(var)),
                dispatch=self.__dispatch
            )
        )


class SettingsCategoryView(OptimizationCategoryView):
    def __init__(
            self,
            dispatch: Dispatch,
            data: OptimizationResultData,
            query: OptimizationQuery
    ):
        super().__init__(dispatch, data, query, "settings")

        self.__dispatch = dispatch

        allows_alternate_recipes = "alternate-recipes" in query.query_vars()
        self.__alternate_recipes_button = discord.ui.Button(
            label="Exclude Alternate Recipes" if allows_alternate_recipes else "Allow Alternate Recipes",
            style=discord.ButtonStyle.danger if allows_alternate_recipes else discord.ButtonStyle.success,
            custom_id="settings_alternate_recipes"
        )
        self.__alternate_recipes_button.callback = self.on_alternate_recipes
        self.add_item(self.__alternate_recipes_button)

        allows_byproducts = not query.strict_outputs()
        self.__byproducts_button = discord.ui.Button(
            label="Exclude Byproducts" if allows_byproducts else "Allow Byproducts",
            style=discord.ButtonStyle.danger if allows_byproducts else discord.ButtonStyle.success,
            custom_id="settings_byproducts"
        )
        self.__byproducts_button.callback = self.on_byproducts
        self.add_item(self.__byproducts_button)

        # TODO: Add button for allowing byproducts

    async def on_alternate_recipes(self, interaction: discord.Interaction):
        print("alternate recipes button clicks")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__dispatch.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        if "alternate-recipes" in query.query_vars():
            query.remove_include("alternate-recipes")
        else:
            query.add_include("alternate-recipes")
        breadcrumbs.add_page(Breadcrumbs.Page(str(query), breadcrumbs.current_page().custom_ids()))
        await self.__dispatch.execute_and_replace(query, breadcrumbs, interaction)

    async def on_byproducts(self, interaction: discord.Interaction):
        print("byproducts clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.__dispatch.parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        query.set_strict_outputs(not query.strict_outputs())
        breadcrumbs.add_page(Breadcrumbs.Page(str(query), breadcrumbs.current_page().custom_ids()))
        await self.__dispatch.execute_and_replace(query, breadcrumbs, interaction)
