import discord.ext
from discord import app_commands
from discord.ext import commands

from .ada import Ada
from .ui.ada_dispatch import AdaDispatch
from .ui.views.compare_recipes_view import CompareRecipesView
from .ui.views.crafter_view import CrafterView
from .ui.views.item_view import ItemView
from .ui.views.multi_entity_view import MultiEntityView
from .ui.views.optimization_view import (
    BuildingsCategoryView, InputCategoryView,
    OptimizationContainer,
    OptimizationSelectorView,
    OutputsCategoryView, RecipesCategoryView, SettingsCategoryView,
)
from .ui.views.recipe_view import RecipeView
from .ui.views.with_previous_view import WithPreviousView


class AdaCog(commands.Cog):
    def __init__(self, bot: commands.Bot, ada_: Ada) -> None:
        self.__bot = bot
        self.__dispatch = AdaDispatch(ada_)
        self._setup_views()

    @app_commands.command(name="ada")
    @discord.app_commands.describe(query="The query you wish to perform. Try /ada help to see examples.")
    async def ada(self, interaction: discord.Interaction, query: str) -> None:
        """ /ada """
        await self.__dispatch.query_and_send(query, interaction)

    @ada.autocomplete('query')
    async def autocomplete_callback(
            self,
            interaction: discord.Interaction,
            current: str
    ) -> list[app_commands.Choice[str]]:
        # Do stuff with the "current" parameter, e.g. querying it search results...
        # Then return a list of app_commands.Choice
        # return [
        #     app_commands.Choice(name='Option 1', value='Option 1')
        # ]
        # if len(current) == 0:
        print("Autocomplete, current:", current)
        if len(current) == 0:
            return [
                app_commands.Choice(name="iron plate", value="iron plate"),
                app_commands.Choice(name="recipes for iron plate", value="recipes for iron plate"),
                app_commands.Choice(name="recipes from iron plate", value="recipes from iron plate"),
                app_commands.Choice(name="compare recipes for iron plate", value="compare recipes for iron plate"),
                app_commands.Choice(name="produce 30 iron plates", value="produce 30 iron plates"),
                app_commands.Choice(
                    name="produce ? iron plates from 30 iron ore",
                    value="produce ? iron plates from 30 iron ore"
                ),
                app_commands.Choice(
                    name="produce ? iron plates from 30 iron ore and alternate recipes",
                    value="produce ? iron plates from 30 iron ore and alternate recipes"
                ),
            ]
        return []

    def _setup_views(self):
        container = OptimizationContainer(self.__dispatch)
        views = [
            ItemView(self.__dispatch),
            CrafterView(self.__dispatch),
            RecipeView(self.__dispatch),
            MultiEntityView([], 0, self.__dispatch),
            OptimizationSelectorView(container, "", None),
            InputCategoryView(container, ""),
            OutputsCategoryView(container, ""),
            RecipesCategoryView(container, ""),
            BuildingsCategoryView(container, ""),
            SettingsCategoryView(container),
            CompareRecipesView(False, self.__dispatch)
        ]
        for view in views:
            self.__bot.add_view(view)
            self.__bot.add_view(WithPreviousView(view, self.__dispatch))
