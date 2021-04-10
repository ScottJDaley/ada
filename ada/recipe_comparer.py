from ada.query import OptimizationQuery
from ada.result import RecipeCompareResult


class RecipeComparer:
    class ProductionStats:
        def __init__(self, inputs, power_consumption, step_count):
            self.inputs = inputs
            self.power_consumption = power_consumption
            self.step_count = step_count

        def to_string(self, indent=0):
            out = []
            out.append("")
            out.append(indent * '  ' + "INPUTS:")
            indent += 1
            for _, (_input, value) in self.inputs.items():
                out.append(indent*'  ' + _input.human_readable_name() +
                           ": " + str(round(value, 2)) + "/m")
            indent -= 1
            out.append(indent * '  ' + "POWER CONSUMPTION:")
            indent += 1
            out.append(indent*'  ' +
                       str(round(self.power_consumption, 2)) + " MW")
            # out.append("PROCESSING STEPS: ")
            # out.append("  " + str(self.step_count))
            return '\n'.join(out)

        def __str__(self):
            return self.to_string()

    class ProductionCompStats:
        def __init__(self, base_production_stats, comp_production_stats, weighted):

            # TODO: Pull this from the same place that the optimizer does
            weighted_resources = {
                "resource:water": 0,
                "resource:iron-ore": 1,
                "resource:copper-ore": 3.29,
                "resource:limestone": 1.47,
                "resource:coal": 2.95,
                "resource:crude-oil": 4.31,
                "resource:bauxite": 8.48,
                "resource:caterium-ore": 6.36,
                "resource:uranium": 46.67,
                "resource:raw-quartz": 6.36,
                "resource:sulfur": 13.33,
            }

            def get_delta_percentage(new, old):
                delta_percentage = "NEW"
                if old is not None and old != 0:
                    delta_percentage = ((new / old) - 1) * 100
                return delta_percentage

            self.resources = {}
            base_resource_total = 0
            for input_var, (_input, value) in base_production_stats.inputs.items():
                self.resources[input_var] = (_input, -100)
                if weighted and input_var in weighted_resources:
                    base_resource_total += value * \
                        weighted_resources[input_var]
                else:
                    base_resource_total += value

            comp_resources_total = 0
            for input_var, (_input, value) in comp_production_stats.inputs.items():
                base_value = None
                if input_var in base_production_stats.inputs:
                    _, base_value = base_production_stats.inputs[input_var]
                self.resources[input_var] = (
                    _input, get_delta_percentage(value, base_value))
                if weighted:
                    comp_resources_total += value * \
                        weighted_resources[input_var]
                else:
                    comp_resources_total += value

            self.resource_requirements = get_delta_percentage(
                comp_resources_total, base_resource_total)

            self.power_consumption = get_delta_percentage(
                comp_production_stats.power_consumption, base_production_stats.power_consumption
            )

            self.complexity = get_delta_percentage(
                comp_production_stats.step_count, base_production_stats.step_count
            )

    class RecipeStats:
        def __init__(self, base, unweighted_stats, weighted_stats):
            self.base = base
            self.unweighted_stats = unweighted_stats
            self.weighted_stats = weighted_stats

        def __str__(self):
            out = []
            out.append("")
            out.append("Base:")
            out.append(str(self.base))
            out.append("")
            out.append("Unweighted")
            out.append(str(self.unweighted_stats))
            out.append("")
            out.append("Weighted")
            out.append(str(self.weighted_stats))
            return '\n'.join(out)

    class RecipeCompStats:
        def __init__(self, base_stats, comp_stats):
            self.unweighted_comp_stats = RecipeComparer.ProductionCompStats(
                base_stats.unweighted_stats, comp_stats.unweighted_stats, False
            )
            self.weighted_comp_stats = RecipeComparer.ProductionCompStats(
                base_stats.weighted_stats, comp_stats.weighted_stats, True
            )

        def to_string(self, indent=0):
            def get_percentage_str(percentage):
                if isinstance(percentage, str):
                    return percentage
                percentage_string = str(round(percentage, 2))
                if percentage > 0:
                    percentage_string = "+" + percentage_string
                return percentage_string + "%"

            out = []
            out.append(indent * '  ' + "Inputs:")
            indent += 1
            # out.append(indent * '  ' + "Unweighted w/o alternates:")
            # indent += 1
            for _, (resource, percentage) in self.unweighted_comp_stats.resources.items():
                out.append(indent*'  ' + resource.human_readable_name() +
                           ": " + get_percentage_str(percentage))
            indent -= 1
            # out.append(indent * '  ' + "Unweighted w/ alternates:")
            # indent += 1
            # for _, (resource, percentage) in self.unweighted_optimal.resources.items():
            #     out.append(indent*'  ' + resource.human_readable_name() +
            #                ": " + get_percentage_str(percentage))
            # indent -= 1
            # out.append(indent * '  ' + "Weighted w/o alternates:")
            # indent += 1
            # for _, (resource, percentage) in self.weighted_default.resources.items():
            #     out.append(indent*'  ' + resource.human_readable_name() +
            #                ": " + get_percentage_str(percentage))
            # indent -= 1
            # out.append(indent * '  ' + "Weighted w/ alternates:")
            # indent += 1
            # for _, (resource, percentage) in self.weighted_optimal.resources.items():
            #     out.append(indent*'  ' + resource.human_readable_name() +
            #                ": " + get_percentage_str(percentage))
            # indent -= 2
            out.append(indent * '  ' + "Total Resource Requirements:")
            indent += 1
            out.append(indent * '  ' + "Unweighted: " +
                       get_percentage_str(self.unweighted_comp_stats.resource_requirements))
            out.append(indent * '  ' + "Weighted: " +
                       get_percentage_str(self.weighted_comp_stats.resource_requirements))
            indent -= 1
            out.append(indent * '  ' + "Power Consumption: " +
                       get_percentage_str(self.unweighted_comp_stats.power_consumption))
            # indent += 1
            # out.append(indent * '  ' + "Unweighted w/o alternates: " +
            #            get_percentage_str(self.unweighted_comp_stats.power_consumption))
            # out.append(indent * '  ' + "Unweighted w/ alternates: " +
            #            get_percentage_str(self.unweighted_optimal.power_consumption))
            # out.append(indent * '  ' + "Weighted w/o alternates: " +
            #            get_percentage_str(self.weighted_default.power_consumption))
            # out.append(indent * '  ' + "Weighted w/ alternates: " +
            #            get_percentage_str(self.weighted_optimal.power_consumption))
            # indent -= 1
            out.append(indent * '  ' + "Complexity: " +
                       get_percentage_str(self.unweighted_comp_stats.complexity))
            # indent += 1
            # out.append(indent * '  ' + "Unweighted w/o alternates: " +
            #            get_percentage_str(self.unweighted_comp_stats.complexity))
            # out.append(indent * '  ' + "Unweighted w/ alternates: " +
            #            get_percentage_str(self.unweighted_optimal.complexity))
            # out.append(indent * '  ' + "Weighted w/o alternates: " +
            #            get_percentage_str(self.weighted_default.complexity))
            # out.append(indent * '  ' + "Weighted w/ alternates: " +
            #            get_percentage_str(self.weighted_optimal.complexity))
            return '\n'.join(out)

        def __str__(self):
            return self.to_string()

    class RelatedRecipeStats:
        def __init__(self, recipe, product_item, recipe_stats, recipe_comp_stats):
            self.recipe = recipe
            self.product_item = product_item
            self.recipe_stats = recipe_stats
            self.recipe_comp_stats = recipe_comp_stats

        def __str__(self):
            out = []
            out.append(self.recipe.human_readable_name())
            out.append(self.recipe_comp_stats.to_string(1))
            return '\n'.join(out)

    class RecipeComparison:
        # comp_recipes is a dictionary: product_item_var -> (product_item, normalized_base_stats, [related_recipe_stats])
        def __init__(self, base_recipe, product_stats):
            self.base_recipe = base_recipe
            self.product_stats = product_stats

        def __str__(self):
            out = []
            out.append("=== Comparing " +
                       self.base_recipe.human_readable_name() + " ===")
            out.append("")
            for product_item_var, (product_item, normalized_stats, related_stats) in self.product_stats.items():
                out.append("For " + product_item.human_readable_name())
                for related_recipe_stats in related_stats:
                    out.append("")
                    out.append(str(related_recipe_stats))
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
            stats.step_count
        )

    def scaled_recipe_stats(self, stats, scalar):
        return self.RecipeStats(
            self.scaled_production_stats(stats.base, scalar),
            self.scaled_production_stats(stats.unweighted_stats, scalar),
            self.scaled_production_stats(stats.weighted_stats, scalar),
        )

    def get_base_stats(self, recipe):
        return self.ProductionStats(
            {
                ingredient.item().var(): (ingredient.item(), ingredient.minute_rate())
                for ingredient in recipe.ingredients().values()
            },
            recipe.crafter().power_consumption(),
            1
        )

    async def compute_production_stats(self, recipe, weighted, allow_alternates):
        inputs = {}

        query = OptimizationQuery("")
        query.maximize_objective = False
        if weighted:
            query.objective_coefficients = {"weighted-resources": -1}
        else:
            query.objective_coefficients = {"unweighted-resources": -1}
        for ingredient_var, ingredient in recipe.ingredients().items():
            if ingredient.item().is_resource():
                inputs[ingredient_var] = (
                    ingredient.item(), ingredient.minute_rate())
            else:
                query.eq_constraints[ingredient_var] = ingredient.minute_rate()

        # Run again, this time disallowing alternate recipes.
        if not allow_alternates:
            query.eq_constraints["alternate-recipes"] = 0

        result = await self.__opt.optimize(query)

        inputs.update(result.inputs())

        return self.ProductionStats(
            inputs,
            -result.net_power() + recipe.crafter().power_consumption(),
            len(result.recipes()) + len(inputs) + 1
        )

    async def compute_recipe_stats(self, recipe):
        base_stats = self.get_base_stats(recipe)
        unweighted_stats = await self.compute_production_stats(recipe, False, False)
        weighted_stats = await self.compute_production_stats(recipe, True, False)
        return self.RecipeStats(
            base_stats,
            unweighted_stats,
            weighted_stats,
        )

    async def compare(self, query):

        # For the base and each related recipe we want to run an optimization query to produce
        # one of the product. We also need to disable all related recipes to force this candidate
        # to be used.

        # The goal is to get, for each candidate recipe, the ingredients, any other products,
        # the raw resources, total power, physical space required, number of steps, etc.

        base_stats = await self.compute_recipe_stats(query.base_recipe)

        # product_var -> (product, normalized_base_stats, [related_recipe_stats])
        product_stats = {}
        for product in query.base_recipe.products().values():
            base_stats_normalized = self.scaled_recipe_stats(
                base_stats, 1 / product.minute_rate())

            related_recipe_stats = []
            for related_recipe in self.__db.recipes_for_product(product.item().var()):
                if related_recipe.var() == query.base_recipe.var():
                    continue

                related_product_minute_rate = 1
                for related_product in related_recipe.products().values():
                    if related_product.item().var() == product.item().var():
                        related_product_minute_rate = related_product.minute_rate()

                related_stats = await self.compute_recipe_stats(related_recipe)
                related_stats_normalized = self.scaled_recipe_stats(
                    related_stats, 1 / related_product_minute_rate)
                # related_recipe_stats[related_recipe.var()] = (
                #     related_recipe, related_stats_normalized)
                comp_stats = self.RecipeCompStats(
                    base_stats_normalized, related_stats_normalized)
                related_recipe_stats.append(self.RelatedRecipeStats(
                    related_recipe, product.item(), related_stats_normalized, comp_stats))

            product_stats[product.item().var()] = (
                product.item(), base_stats_normalized, related_recipe_stats
            )

            recipe_comparison_stats = self.RecipeComparison(
                query.base_recipe, product_stats)

            print(recipe_comparison_stats)

        return RecipeCompareResult("compare result")
