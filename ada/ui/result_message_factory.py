import discord
import tabulate
from multimethod import multimethod

from .breadcrumbs import Breadcrumbs
from .dispatch import Dispatch
from .result_message import ResultMessage
from .views.compare_recipes_view import CompareRecipesView
from .views.crafter_view import CrafterView
from .views.item_view import ItemView
from .views.multi_entity_view import MultiEntityView
from .views.optimization_view import OptimizationSelectorView
from .views.recipe_view import RecipeView
from ..db.crafter import Crafter
from ..db.extractor import Extractor
from ..db.item import Item
from ..db.power_generator import PowerGenerator
from ..db.power_recipe import PowerRecipe
from ..db.recipe import Recipe
from ..help import HelpResult
from ..info import InfoResult
from ..optimization_result_data import OptimizationResultData
from ..optimizer import OptimizationResult
from ..recipe_comparer import RecipeCompareResult
from ..result import ErrorResult, Result


# noinspection PyMethodParameters
class ResultMessageFactory:
    @staticmethod
    def from_result(result: Result, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        message = ResultMessageFactory._from_result(result, breadcrumbs, dispatch)
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
            start_index = int(breadcrumbs.current_page().custom_ids()[0])
            message.view = MultiEntityView(entities, start_index, dispatch)
            return message

        entity = entities[0]
        breadcrumbs.current_page().replace_query(entity.var())
        return ResultMessageFactory._from_entity(entity, breadcrumbs, dispatch)

    @multimethod
    def _from_result(result: OptimizationResult, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
        print("_from_result: OptimizationResult")
        if len(breadcrumbs.current_page().custom_ids()) == 0:
            breadcrumbs.current_page().add_custom_id("settings")
        breadcrumbs.current_page().replace_query(str(result.query()))
        message = ResultMessage(breadcrumbs)
        if not result.success():
            message.embed = discord.Embed(title=str(result))
            message.view = OptimizationSelectorView.get_view(
                breadcrumbs,
                dispatch,
                OptimizationResultData(inputs={}, outputs={}, recipes={}, crafters={}, generators={}, net_power=0),
                result.query()
            )
            return message

        message.embed = discord.Embed(title="Optimization Query")

        result_data = result.result_data()
        inputs = [f"{input.human_readable_name()}: {round(abs(amount), 2)}"
                  for input, amount in result_data.inputs().values()]
        outputs = [f"{output.human_readable_name()}: {round(abs(amount), 2)}"
                   for output, amount in result_data.outputs().values()]
        recipes = [f"{recipe.human_readable_name()}: {round(abs(amount), 2)}"
                   for recipe, amount in result_data.recipes().values()]
        buildings = [f"{crafter.human_readable_name()}: {round(abs(amount), 2)}"
                     for crafter, amount in result_data.crafters().values()]
        buildings.extend(
            [f"{generator.human_readable_name()}: {round(abs(amount), 2)}"
             for generator, amount in result_data.generators().values()]
        )

        sections = [str(result.query())]
        if len(inputs) > 0:
            sections.append("**Inputs**\n" + "\n".join(inputs))
        if len(outputs) > 0:
            sections.append("**Outputs**\n" + "\n".join(outputs))
        if len(recipes) > 0:
            sections.append("**Recipes**\n" + "\n".join(recipes))
        if len(buildings) > 0:
            sections.append("**Buildings**\n" + "\n".join(buildings))

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
        query = result.stats().query
        breadcrumbs.current_page().replace_query(str(query))
        message = ResultMessage(breadcrumbs)
        message.embed = None

        product_name = query.product_item.human_readable_name()

        alternates_str = "\n*The above stats and requirements are computed from optimal production chains that " \
                         "may include alternate recipes.*"

        no_alternates_str = "\n*The above stats and requirements are computed from optimal production chains using " \
                            "only base recipes.*"

        out = [
            f"**Recipe Stats:**",
            f"```\n{tabulate.tabulate(result.overall_stats(), headers='keys', tablefmt='simple')}```",
            f"**Recipe Requirements:**",
            f"```\n{tabulate.tabulate(result.input_stats(), headers='keys', tablefmt='simple')}```",
            alternates_str if query.include_alternates else no_alternates_str
        ]

        message.content = "\n".join(out)
        if len(message.content) > 2000:
            message.content = "Output was too long"
        message.view = CompareRecipesView(query.include_alternates, dispatch)
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
        if len(entity.products()) == 1:
            product = next(iter(entity.products().values()))
            message.embed.set_thumbnail(url=product.item().thumb())
        for name, value in entity.fields():
            message.embed.add_field(name=name, value=value, inline=True)
        message.view = RecipeView(dispatch)
        return message
