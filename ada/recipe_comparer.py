from .compare_recipes_for import (
    CompareRecipesForQuery,
    ProductionStats,
    RecipeCompStats,
    RecipeComparison,
    RecipeStats,
    RelatedRecipeStats,
)
from .db.db import DB
from .db.recipe import Recipe
from .optimization_query import AmountValue, MaximizeValue, OptimizationQuery
from .optimizer import Optimizer


class RecipeComparer:
    def __init__(self, db: DB, opt: Optimizer) -> None:
        self.__db = db
        self.__opt = opt

    @staticmethod
    def scaled_production_stats(
            stats: ProductionStats, scalar: float
    ) -> ProductionStats:
        return ProductionStats(
            {
                input_var: (item, value * scalar)
                for input_var, (item, value) in stats.inputs.items()
            },
            stats.power_consumption * scalar,
            stats.step_count,
        )

    @staticmethod
    def scaled_recipe_stats(stats: RecipeStats, scalar: float) -> RecipeStats:
        return RecipeStats(
            RecipeComparer.scaled_production_stats(stats.base, scalar),
            RecipeComparer.scaled_production_stats(stats.unweighted_stats, scalar),
            RecipeComparer.scaled_production_stats(stats.weighted_stats, scalar),
        )

    @staticmethod
    def get_base_stats(recipe: Recipe) -> ProductionStats:
        return ProductionStats(
            {
                ingredient.item().var(): (ingredient.item(), ingredient.minute_rate())
                for ingredient in recipe.ingredients().values()
            },
            recipe.crafter().power_consumption(),
            1,
        )

    async def compute_production_stats(
            self, recipe: Recipe, weighted: bool, include_alternates: bool
    ) -> ProductionStats:
        inputs = {}

        query = OptimizationQuery()
        var = "weighted-resources" if weighted else "unweighted-resources"
        query.add_input(var, MaximizeValue(), False)

        for ingredient_var, ingredient in recipe.ingredients().items():
            if ingredient.item().is_resource():
                inputs[ingredient_var] = (ingredient.item(), ingredient.minute_rate())
            else:
                # query.eq_constraints[ingredient_var] = ingredient.minute_rate()
                query.add_output(ingredient_var, AmountValue(ingredient.minute_rate()), False)

        if include_alternates:
            query.add_input("alternate-recipes")

        result = await self.__opt.optimize(query)

        inputs.update(result.result_data().inputs())

        return ProductionStats(
            inputs,
            -result.result_data().net_power() + recipe.crafter().power_consumption(),
            len(result.result_data().recipes()) + len(inputs) + 1,
        )

    async def compute_recipe_stats(
            self, recipe: Recipe, include_alternates: bool
    ) -> RecipeStats:
        base_stats = self.get_base_stats(recipe)
        unweighted_stats = await self.compute_production_stats(
            recipe, False, include_alternates
        )
        weighted_stats = await self.compute_production_stats(
            recipe, True, include_alternates
        )
        return RecipeStats(
            base_stats,
            unweighted_stats,
            weighted_stats,
        )

    async def compare(self, query: CompareRecipesForQuery) -> RecipeComparison:

        # For the base and each related recipe we want to run an optimization query to produce
        # one of the product. We also need to disable all related recipes to force this candidate
        # to be used.

        # The goal is to get, for each candidate recipe, the ingredients, any other products,
        # the raw resources, total power, physical space required, number of steps, etc.

        base_stats = await self.compute_recipe_stats(
            query.base_recipe, query.include_alternates
        )

        product = query.base_recipe.products()[query.product_item.var()]

        base_stats_normalized = self.scaled_recipe_stats(
            base_stats, 1 / product.minute_rate()
        )

        related_recipe_stats = []
        for related_recipe in query.related_recipes:
            if related_recipe.var() == query.base_recipe.var():
                continue

            related_product_minute_rate = 1
            for related_product in related_recipe.products().values():
                if related_product.item().var() == query.product_item.var():
                    related_product_minute_rate = related_product.minute_rate()

            related_stats = await self.compute_recipe_stats(
                related_recipe, query.include_alternates
            )
            related_stats_normalized = self.scaled_recipe_stats(
                related_stats, 1 / related_product_minute_rate
            )
            # related_recipe_stats[related_recipe.var()] = (
            #     related_recipe, related_stats_normalized)
            comp_stats = RecipeCompStats(
                base_stats_normalized, related_stats_normalized
            )
            related_recipe_stats.append(
                RelatedRecipeStats(
                    related_recipe, product.item(), related_stats_normalized, comp_stats
                )
            )

        return RecipeComparison(query, base_stats_normalized, related_recipe_stats)
