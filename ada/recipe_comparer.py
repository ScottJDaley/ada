from ada.query import OptimizationQuery
from ada.result import RecipeCompareResult


class RecipeComparer:
    class ProductionStats:
        def __init__(self, inputs, power_consumption, step_count, relative_to=None):
            self.inputs = inputs
            self.power_consumption = power_consumption
            self.step_count = step_count
            self.relative_to = relative_to

        def __str__(self):

            def get_delta_percentage(new, old):
                delta_percentage = 100
                if other_value != 0:
                    delta_percentage = ((value / other_value) - 1) * 100
                percentage_string = str(round(delta_percentage, 2))
                if delta_percentage > 0:
                    percentage_string = "+" + percentage_string
                return " (" + percentage_string + "%)"

            out = []
            out.append("")
            out.append("INPUTS:")
            for input_var, (_input, value) in self.inputs.items():
                out.append("  " + _input.human_readable_name() +
                           ": " + str(round(value, 2)) + "/m")
                if self.relative_to is not None:
                    other_value = 0
                    if input_var in self.relative_to.inputs:
                        _, other_value = self.relative_to.inputs[input_var]
                    out[-1] += get_delta_percentage(value, other_value)
            out.append("POWER CONSUMPTION:")
            out.append("  " + str(self.power_consumption) + " MW")
            out.append("PROCESSING STEPS: ")
            out.append("  " + str(self.step_count))
            return '\n'.join(out)

    class RecipeStats:
        def __init__(self, base, default, optimal):
            self.base = base
            self.default = default
            self.optimal = optimal

        def __str__(self):
            out = []
            out.append("")
            out.append("Base:")
            out.append(str(self.base))
            out.append("")
            out.append(
                "From raw (optimal productivity without alternate recipes)")
            out.append(str(self.default))
            out.append("")
            out.append(
                "From raw (optimal productivity with alternate recipes): ")
            out.append(str(self.optimal))
            return '\n'.join(out)

    class RecipeComparisonStats:
        def __init__(self, base_recipe, base_stats, related_stats):
            self.base_recipe = base_recipe
            self.base_stats = base_stats
            self.related_stats = related_stats

        def __str__(self):
            out = []
            out.append("")
            out.append(self.base_recipe.human_readable_name())
            out.append(str(self.base_stats))
            for _, (recipe, recipe_stats) in self.related_stats.items():
                out.append("")
                out.append(recipe.human_readable_name())
                out.append(str(recipe_stats))
            return '\n'.join(out)

    def __init__(self, db, opt):
        self.__db = db
        self.__opt = opt

    def scaled_production_stats(self, stats, scalar):
        return self.ProductionStats(
            {
                input_var: (item, value * scalar)
                for input_var, (item, value) in stats.inputs.items()
            },
            stats.power_consumption * scalar,
            stats.step_count,
            self.scaled_production_stats(
                stats.relative_to, scalar) if stats.relative_to is not None else None
        )

    def scaled_recipe_stats(self, stats, scalar):
        return self.RecipeStats(
            self.scaled_production_stats(stats.base, scalar),
            self.scaled_production_stats(stats.default, scalar),
            self.scaled_production_stats(stats.optimal, scalar),
        )

    def get_base_stats(self, recipe, relative_to=None):
        return self.ProductionStats(
            {
                ingredient.item().var(): (ingredient.item(), ingredient.minute_rate())
                for ingredient in recipe.ingredients().values()
            },
            recipe.crafter().power_consumption(),
            1,
            relative_to
        )

    async def compute_production_stats(self, recipe, exclude_alternate_recipes, relative_to=None):
        query = OptimizationQuery("")
        query.maximize_objective = False
        query.objective_coefficients = {"unweighted-resources": -1}
        for ingredient_var, ingredient in recipe.ingredients().items():
            query.eq_constraints[ingredient_var] = ingredient.minute_rate()

        # optimal_result = await self.__opt.optimize(query)

        # Run again, this time disallowing alternate recipes.
        if exclude_alternate_recipes:
            query.eq_constraints["alternate-recipes"] = 0

        result = await self.__opt.optimize(query)

        print(result)

        return self.ProductionStats(
            result.inputs(),
            -result.net_power() + recipe.crafter().power_consumption(),
            len(result.recipes()) + len(result.inputs()) + 1,
            relative_to
        )

    async def compute_recipe_stats(self, recipe, relative_to=None):
        base_stats = self.get_base_stats(
            recipe, relative_to.base if relative_to else None)
        default_stats = await self.compute_production_stats(recipe, True, relative_to.default if relative_to is not None else None)
        optimal_stats = await self.compute_production_stats(recipe, False, relative_to.optimal if relative_to is not None else None)
        return self.RecipeStats(base_stats, default_stats, optimal_stats)

    async def compare(self, query):

        # For the base and each related recipe we want to run an optimization query to produce
        # one of the product. We also need to disable all related recipes to force this candidate
        # to be used.

        # The goal is to get, for each candidate recipe, the ingredients, any other products,
        # the raw resources, total power, physical space required, number of steps, etc.

        print("=== Base Stats ===")
        base_stats = await self.compute_recipe_stats(query.base_recipe)
        print(base_stats)

        for product in query.base_recipe.products().values():
            print("=== Evaluating for",
                  product.item().human_readable_name(), "product ===")

            print("=== Base Stats Normalized ===")
            base_stats_normalized = self.scaled_recipe_stats(
                base_stats, 1 / product.minute_rate())
            print(base_stats_normalized)

            related_recipe_stats = {}
            for related_recipe in self.__db.recipes_for_product(product.item().var()):
                if related_recipe.var() == query.base_recipe.var():
                    continue
                print("\nFound related recipe: " +
                      related_recipe.human_readable_name())

                related_product_minute_rate = 1
                for related_product in related_recipe.products().values():
                    if related_product.item().var() == product.item().var():
                        related_product_minute_rate = related_product.minute_rate()

                print("=== Related Base Stats Normalized ===")
                related_stats = await self.compute_recipe_stats(related_recipe, base_stats)
                related_stats_normalized = self.scaled_recipe_stats(
                    related_stats, 1 / related_product_minute_rate)
                print(related_stats_normalized)
                related_recipe_stats[related_recipe.var()] = (
                    related_recipe, related_stats_normalized)

            recipe_comparison_stats = self.RecipeComparisonStats(
                query.base_recipe, base_stats_normalized, related_recipe_stats)
            print(recipe_comparison_stats)

        return RecipeCompareResult("compare result")
