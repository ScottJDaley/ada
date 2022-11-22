import discord
import tabulate
from multimethod import multimethod

from .breadcrumbs import Breadcrumbs
from .dispatch import Dispatch
from .result_message import ResultMessage
from .views.crafter_view import CrafterView
from .views.item_view import ItemView
from .views.multi_entity_view import MultiEntityView
from .views.optimization_view import OptimizationSelectorView
from .views.recipe_view import RecipeView
from .views.with_previous_view import WithPreviousView
from ..db.buildable_recipe import BuildableRecipe
from ..db.crafter import Crafter
from ..db.extractor import Extractor
from ..db.item import Item
from ..db.power_generator import PowerGenerator
from ..db.power_recipe import PowerRecipe
from ..db.recipe import Recipe
from ..help import HelpResult
from ..info import InfoResult
from ..optimizer import OptimizationResult
from ..recipe_comparer import RecipeCompareResult
from ..result import ErrorResult, Result


# noinspection PyMethodParameters
class ResultMessageFactory:
    @staticmethod
    def from_result(result: Result, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        message = ResultMessageFactory._from_result(result, breadcrumbs, dispatch)
        if message.breadcrumbs.has_prev_page():
            message.view = WithPreviousView(message.view, dispatch)
        return message

    @multimethod
    def _from_result(result: HelpResult, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title="Help")
        message.embed.description = str(result)
        return message

    @multimethod
    def _from_result(result: ErrorResult, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title="Error")
        message.embed.description = result.error_message()
        return message

    @multimethod
    def _from_result(result: InfoResult, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        entities = result.entities()

        if len(entities) == 0:
            message = ResultMessage(breadcrumbs)
            message.embed = discord.Embed(title="No matches found")
            return message

        if len(entities) > 1:
            message = ResultMessage(breadcrumbs)
            message.embed = None
            message.file = None
            if len(breadcrumbs.current_page().custom_ids()) == 0:
                breadcrumbs.current_page().add_custom_id("0")
            message.view = MultiEntityView(entities, breadcrumbs.current_page().custom_ids()[0], dispatch)
            return message

        entity = entities[0]
        breadcrumbs.current_page().replace_query(entity.var())
        return ResultMessageFactory._from_entity(entity, breadcrumbs, dispatch)

    @multimethod
    def _from_result(result: OptimizationResult, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        print("_from_result: OptimizationResult")
        if not result.success():
            message = ResultMessage(breadcrumbs)
            message.embed = discord.Embed(title=str(result))
            return message

        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title="Optimization Query")

        sections = [str(result.query())]

        result_data = result.result_data()

        # descriptions = []
        description = ""
        for section in sections:
            # TODO: Handle this another way
            # if len(curr_description) + len(section) >= 4096:
            #     descriptions.append(curr_description)
            #     curr_description = ""
            description += section + "\n\n"
        # descriptions.append(curr_description)

        message.embed.description = description

        filename = "output.gv"
        filepath = "output/" + filename
        result.generate_graph_viz(filepath)
        file = discord.File(filepath + ".png")
        # The image already shows up from the attached file, so no need to place it in the embed as well.
        message.embed.set_image(url="attachment://" + filename + ".png")
        message.file = file
        if len(breadcrumbs.current_page().custom_ids()) == 0:
            breadcrumbs.current_page().add_custom_id("inputs")
        breadcrumbs.current_page().replace_query(str(result.query()))
        message.view = OptimizationSelectorView.get_view(
            breadcrumbs,
            dispatch,
            result_data,
            result.query()
        )
        return message

    @staticmethod
    @multimethod
    def _from_result(result: RecipeCompareResult, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        message = ResultMessage(breadcrumbs)
        message.embed = None

        product_name = result.stats().query.product_item.human_readable_name()

        out = [
            "All recipes that produce " + product_name, "```\n{}```".format(
                tabulate.tabulate(result.overall_stats(), headers="keys", tablefmt="simple")
            ),
            "Raw Inputs for 1/m " + product_name, "```\n{}```".format(
                tabulate.tabulate(result.input_stats(), headers="keys", tablefmt="simple")
            )
        ]

        message.content = "\n".join(out)
        if len(message.content) > 2000:
            message.content = "Output was too long"
        return message

    # @staticmethod
    # @multimethod
    # def _from_result(result: Result, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
    #     message = ResultMessage(breadcrumbs)
    #     message.embed = discord.Embed(title="Unknown Result Type")
    #     message.embed.description = str(result)
    #     return message

    @multimethod
    def _from_entity(entity: BuildableRecipe, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        # TODO: Add view
        return message

    @multimethod
    def _from_entity(entity: Crafter, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        message.embed.url = entity.wiki()
        message.embed.set_thumbnail(url=entity.thumb())
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        message.view = CrafterView(dispatch)
        return message

    @multimethod
    def _from_entity(entity: Extractor, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        message.embed.url = entity.wiki()
        message.embed.set_thumbnail(url=entity.thumb())
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        # TODO: Add view
        return message

    @multimethod
    def _from_entity(entity: Item, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        message.embed.url = entity.wiki()
        message.embed.set_thumbnail(url=entity.thumb())
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        message.view = ItemView(dispatch)
        return message

    @multimethod
    def _from_entity(entity: PowerGenerator, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        message.embed.url = entity.wiki()
        message.embed.set_thumbnail(url=entity.thumb())
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        # TODO: Add view
        return message

    @multimethod
    def _from_entity(entity: PowerRecipe, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        # TODO: Add view
        return message

    @staticmethod
    @multimethod
    def _from_entity(entity: Recipe, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
        message = ResultMessage(breadcrumbs)
        message.embed = discord.Embed(title=entity.human_readable_name())
        message.embed.description = entity.description()
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        message.view = RecipeView(dispatch)
        return message

    # @staticmethod
    # @multimethod
    # def _from_entity(entity: Entity, breadcrumbs: Breadcrumbs, dispatch: Dispatch):
    #     message = ResultMessage(breadcrumbs)
    #     message.embed = discord.Embed(title="Unknown Entity Type")
    #     message.embed.description = str(entity)
    #     return message
