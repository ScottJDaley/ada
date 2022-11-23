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
    async def help(self, interaction: discord.Interaction, query: str) -> None:
        """ /ada """
        await self.__dispatch.query_and_send(query, interaction)

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
