from functools import partial
from typing import Awaitable, Callable, Optional, cast

import discord

from ..breadcrumbs import Breadcrumbs
from ..dispatch import Dispatch
from ..result_message import ResultMessage
from ...db.entity import Entity
from ...optimization_query import MaximizeValue, OptimizationQuery
from ...optimization_result_data import OptimizationResultData
from ...optimizer import OptimizationResult
from ...query_parser import QueryParseException


# TODO: Finish up persistence work here:
class OptimizationContainer:
    def __init__(
            self,
            dispatch: Dispatch,
            data: Optional[OptimizationResultData] = None,
            query: Optional[OptimizationQuery] = None
    ):
        self.__dispatch = dispatch
        self.__data = data
        self.__query = query

    def dispatch(self) -> Dispatch:
        return self.__dispatch

    def query(self, breadcrumbs: Breadcrumbs) -> OptimizationQuery:
        if not self.__query:
            self._restore_query(breadcrumbs)
        return self.__query

    async def data(self, breadcrumbs: Breadcrumbs) -> OptimizationResultData:
        if not self.__data:
            await self._restore_data(breadcrumbs)
        return self.__data

    def try_get_query(self) -> Optional[OptimizationQuery]:
        return self.__query

    def try_get_data(self) -> Optional[OptimizationResultData]:
        return self.__data

    def _restore_query(self, breadcrumbs: Breadcrumbs) -> None:
        raw_query = breadcrumbs.current_page().query()
        query = self.__dispatch.parse(raw_query)
        self.__query = cast(OptimizationQuery, query)

    async def _restore_data(self, breadcrumbs: Breadcrumbs) -> None:
        result = await self.__dispatch.execute(self.query(breadcrumbs))
        result = cast(OptimizationResult, result)
        self.__data = result.result_data()


# Note:         # discord.utils.get(self.children, custom_id="input_info")


class OptimizationView(discord.ui.View):
    def __init__(self, container: OptimizationContainer):
        super().__init__(timeout=None)
        self.__container = container

    def dispatch(self) -> Dispatch:
        return self.__container.dispatch()

    def query(self, breadcrumbs: Breadcrumbs) -> OptimizationQuery:
        return self.__container.query(breadcrumbs)

    async def data(self, breadcrumbs: Breadcrumbs) -> OptimizationResultData:
        return await self.__container.data(breadcrumbs)

    def try_get_query(self) -> Optional[OptimizationQuery]:
        return self.__container.try_get_query()

    def try_get_data(self) -> Optional[OptimizationResultData]:
        return self.__container.try_get_data()


class OptimizationCategoryView(OptimizationView):
    def __init__(
            self,
            container: OptimizationContainer,
            active_category: str,
    ):
        super().__init__(container)
        self._add_categories(active_category)

    def _add_categories(self, active_category: str):
        print("Adding category buttons")
        for category in ["Settings", "Inputs", "Outputs", "Recipes", "Buildings"]:
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
        message = ResultMessage.copy_from(interaction)
        message.breadcrumbs.current_page().clear_custom_ids()
        message.breadcrumbs.current_page().add_custom_id(custom_id)
        message.view = OptimizationSelectorView.get_view(
            message.breadcrumbs,
            self.dispatch(),
            await self.data(message.breadcrumbs),
            self.query(message.breadcrumbs)
        )
        await message.replace(interaction, self.dispatch())


class EntityDropdown(discord.ui.Select):
    def __init__(
            self,
            entities: list[Entity],
            placeholder: str,
            dispatch: Dispatch,
            callback: Callable[[str, discord.Interaction], Awaitable[None]]
    ):
        self.__dispatch = dispatch
        self.__callback = callback
        options = []
        for entity in entities:
            options.append(discord.SelectOption(label=entity.var(), description=entity.human_readable_name()))
        if len(options) == 0:
            options.append(discord.SelectOption(label="None"))
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            custom_id="optimization_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        print("EntityDropdown callback")
        selection_option = self.values[0]
        print("Selected option", self.values[0])
        await self.__callback(selection_option, interaction)


class OptimizationSelectorView(OptimizationCategoryView):
    def __init__(
            self,
            container: OptimizationContainer,
            category: str,
            placeholder: Optional[str],
    ):
        super().__init__(container, category)
        entities: list[Entity] = []
        data = self.try_get_data()
        if data:
            if category == "inputs":
                for item, _ in data.inputs().values():
                    entities.append(item)
                if not placeholder:
                    placeholder = "Select an input"
            elif category == "outputs":
                for item, _ in data.outputs().values():
                    entities.append(item)
                if not placeholder:
                    placeholder = "Select an output"
            elif category == "recipes":
                for recipe, _ in data.recipes().values():
                    entities.append(recipe)
                if not placeholder:
                    placeholder = "Select a recipe"
            elif category == "buildings":
                for crafter, _ in data.crafters().values():
                    entities.append(crafter)
                for generator, _ in data.generators().values():
                    entities.append(generator)
                if not placeholder:
                    placeholder = "Select a building"
        # TODO: add cases for other categories
        self.add_item(EntityDropdown(entities, placeholder, self.dispatch(), self.on_select))

    @staticmethod
    def get_view(
            breadcrumbs: Breadcrumbs, dispatch: Dispatch, data: OptimizationResultData,
            query: OptimizationQuery
    ) -> discord.ui.View:
        custom_ids = breadcrumbs.current_page().custom_ids()
        category = custom_ids[0]
        container = OptimizationContainer(dispatch, data, query)
        if category == "settings":
            return SettingsCategoryView(container)
        if len(breadcrumbs.current_page().custom_ids()) != 2:
            return OptimizationSelectorView(container, category, None)
        selected = custom_ids[1]
        if category == "inputs":
            return InputCategoryView(container, selected)
        if category == "outputs":
            return OutputsCategoryView(container, selected)
        if category == "recipes":
            return RecipesCategoryView(container, selected)
        if category == "buildings":
            return BuildingsCategoryView(container, selected)
        return OptimizationSelectorView(container, category, None)

    async def on_select(self, selected: str, interaction: discord.Interaction):
        if selected == "None":
            print("Selected None")
            await interaction.response.defer()
            return
        message = ResultMessage.copy_from(interaction)
        custom_ids = message.breadcrumbs.current_page().custom_ids()
        if len(custom_ids) < 2:
            message.breadcrumbs.current_page().add_custom_id(selected)
        else:
            custom_ids[1] = selected
        message.view = OptimizationSelectorView.get_view(
            message.breadcrumbs,
            self.dispatch(),
            await self.data(message.breadcrumbs),
            self.query(message.breadcrumbs)
        )
        await message.replace(interaction, self.dispatch())


class InfoButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str, dispatch: Dispatch):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=custom_id, emoji="ℹ")
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
            container: OptimizationContainer,
            selected: str
    ):
        super().__init__(container, "inputs", selected)

        input_name = ""
        amount = 0

        data = self.try_get_data()
        if data:
            input, amount = data.inputs()[selected]
            input_name = input.human_readable_name()

        self.add_item(InfoButton(label=input_name, custom_id="input_info", dispatch=self.dispatch()))

        # self.add_item(
        #     discord.ui.Button(
        #         label=str(amount),
        #         style=discord.ButtonStyle.secondary,
        #         custom_id="input_amount",
        #         disabled=True
        #     )
        # )

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
                dispatch=self.dispatch()
            )
        )

    async def on_minimize(self, interaction: discord.Interaction):
        print("minimize button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.dispatch().parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        input_var = breadcrumbs.current_page().custom_ids()[-1]
        query.remove_input(input_var)
        query.add_input(input_var, MaximizeValue(), False)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        await self.dispatch().execute_and_replace(query, breadcrumbs, interaction)


class OutputsCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            container: OptimizationContainer,
            selected: str
    ):
        super().__init__(container, "outputs", selected)

        output_name = ""
        amount = 0

        data = self.try_get_data()
        if data:
            output, amount = data.outputs()[selected]
            output_name = output.human_readable_name()

        self.add_item(InfoButton(label=output_name, custom_id="output_info", dispatch=self.dispatch()))

        # self.__amount_button = discord.ui.Button(
        #     label=str(amount),
        #     style=discord.ButtonStyle.secondary,
        #     custom_id="output_amount",
        #     disabled=True
        # )
        # self.add_item(self.__amount_button)

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
                dispatch=self.dispatch()
            )
        )

    async def on_maximize(self, interaction: discord.Interaction):
        print("maximize button clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.dispatch().parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        output_var = breadcrumbs.current_page().custom_ids()[-1]
        query.remove_output(output_var)
        query.add_output(output_var, MaximizeValue(), False)
        breadcrumbs.add_page(Breadcrumbs.Page(str(query)))
        await self.dispatch().execute_and_replace(query, breadcrumbs, interaction)


class RecipesCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            container: OptimizationContainer,
            selected: str
    ):
        super().__init__(container, "recipes", selected)

        recipe_name = ""
        amount = 0

        data = self.try_get_data()
        if data:
            recipe, amount = data.recipes()[selected]
            recipe_name = recipe.human_readable_name()

        self.add_item(InfoButton(label=recipe_name, custom_id="recipe_info", dispatch=self.dispatch()))

        # self.__amount_button = discord.ui.Button(
        #     label=str(amount),
        #     style=discord.ButtonStyle.secondary,
        #     custom_id="recipe_amount",
        #     disabled=True
        # )
        # self.add_item(self.__amount_button)

        self.add_item(
            EditQueryButton(
                custom_id="recipe_exclude",
                edit_query=(lambda q, var: q.add_exclude(var)),
                dispatch=self.dispatch()
            )
        )


class BuildingsCategoryView(OptimizationSelectorView):
    def __init__(
            self,
            container: OptimizationContainer,
            selected: str
    ):
        super().__init__(container, "buildings", selected)

        building_name = ""
        amount = 0

        data = self.try_get_data()
        if data:
            if selected in data.crafters():
                building, amount = data.crafters()[selected]
            else:
                building, amount = data.generators()[selected]
            building_name = building.human_readable_name()

        self.add_item(InfoButton(label=building_name, custom_id="building_info", dispatch=self.dispatch()))

        # self.__amount_button = discord.ui.Button(
        #     label=str(amount),
        #     style=discord.ButtonStyle.secondary,
        #     custom_id="building_amount",
        #     disabled=True
        # )
        # self.add_item(self.__amount_button)

        self.add_item(
            EditQueryButton(
                custom_id="building_exclude",
                edit_query=(lambda q, var: q.add_exclude(var)),
                dispatch=self.dispatch()
            )
        )


class SettingsCategoryView(OptimizationCategoryView):
    def __init__(
            self,
            container: OptimizationContainer,
    ):
        super().__init__(container, "settings")

        query = self.try_get_query()
        if not query:
            # Create a dummy query here just so that we create all the buttons correctly.
            query = OptimizationQuery()

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
            query = self.dispatch().parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        if "alternate-recipes" in query.query_vars():
            query.remove_include("alternate-recipes")
        else:
            query.add_include("alternate-recipes")
        breadcrumbs.add_page(Breadcrumbs.Page(str(query), breadcrumbs.current_page().custom_ids()))
        await self.dispatch().execute_and_replace(query, breadcrumbs, interaction)

    async def on_byproducts(self, interaction: discord.Interaction):
        print("byproducts clicked")
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        raw_query = breadcrumbs.current_page().query()
        try:
            query = self.dispatch().parse(raw_query)
        except QueryParseException as parse_exception:
            print(f"Failed to parse {raw_query}: {parse_exception}")
            return
        query = cast(OptimizationQuery, query)
        query.set_strict_outputs(not query.strict_outputs())
        breadcrumbs.add_page(Breadcrumbs.Page(str(query), breadcrumbs.current_page().custom_ids()))
        await self.dispatch().execute_and_replace(query, breadcrumbs, interaction)
