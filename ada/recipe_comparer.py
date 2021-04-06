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
                delta_percentage = 100
                if old != 0:
                    delta_percentage = ((new / old) - 1) * 100
                return delta_percentage

            self.resources = {}
            base_resource_total = 0
            for input_var, (_input, value) in base_production_stats.inputs.items():
                print(input_var)
                self.resources[input_var] = (_input, -100)
                if weighted and input_var in weighted_resources:
                    base_resource_total += value * \
                        weighted_resources[input_var]
                else:
                    base_resource_total += value

            comp_resources_total = 0
            for input_var, (_input, value) in comp_production_stats.inputs.items():
                base_value = 0
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
        def __init__(self, base, unweighted_default, unweighted_optimal, weighted_default, weighted_optimal):
            self.base = base
            self.unweighted_default = unweighted_default
            self.unweighted_optimal = unweighted_optimal
            self.weighted_default = weighted_default
            self.weighted_optimal = weighted_optimal

        def __str__(self):
            out = []
            out.append("")
            out.append("Base:")
            out.append(str(self.base))
            out.append("")
            out.append("Unweighted w/o alternates")
            out.append(str(self.unweighted_default))
            out.append("")
            out.append("Unweighted w/ alternates")
            out.append(str(self.unweighted_optimal))
            out.append("")
            out.append("Weighted w/o alternates")
            out.append(str(self.weighted_default))
            out.append("")
            out.append("Weighted w/ alternates")
            out.append(str(self.weighted_optimal))
            return '\n'.join(out)

    class RecipeCompStats:
        def __init__(self, base_stats, comp_stats):
            self.unweighted_default = RecipeComparer.ProductionCompStats(
                base_stats.unweighted_default, comp_stats.unweighted_default, False
            )
            self.unweighted_optimal = RecipeComparer.ProductionCompStats(
                base_stats.unweighted_optimal, comp_stats.unweighted_optimal, False
            )
            self.weighted_default = RecipeComparer.ProductionCompStats(
                base_stats.weighted_default, comp_stats.weighted_default, True
            )
            self.weighted_optimal = RecipeComparer.ProductionCompStats(
                base_stats.weighted_optimal, comp_stats.weighted_optimal, True
            )

        def to_string(self, indent=0):
            def get_percentage_str(percentage):
                percentage_string = str(round(percentage, 2))
                if percentage > 0:
                    percentage_string = "+" + percentage_string
                return percentage_string + "%"

            out = []
            # out.append(indent * '  ' + "Resource Requirements:")
            # indent += 1
            # out.append(indent * '  ' + "Unweighted w/o alternates:")
            # indent += 1
            # for _, (resource, percentage) in self.unweighted_default.resources.items():
            #     out.append(indent*'  ' + resource.human_readable_name() +
            #                ": " + get_percentage_str(percentage))
            # indent -= 1
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
            out.append(indent * '  ' + "Resource Requirements:")
            indent += 1
            out.append(indent * '  ' + "Unweighted w/o alternates: " +
                       get_percentage_str(self.unweighted_default.resource_requirements))
            out.append(indent * '  ' + "Unweighted w/ alternates: " +
                       get_percentage_str(self.unweighted_optimal.resource_requirements))
            out.append(indent * '  ' + "Weighted w/o alternates: " +
                       get_percentage_str(self.weighted_default.resource_requirements))
            out.append(indent * '  ' + "Weighted w/ alternates: " +
                       get_percentage_str(self.weighted_optimal.resource_requirements))
            indent -= 1
            out.append(indent * '  ' + "Power Consumption:")
            indent += 1
            out.append(indent * '  ' + "Unweighted w/o alternates: " +
                       get_percentage_str(self.unweighted_default.power_consumption))
            out.append(indent * '  ' + "Unweighted w/ alternates: " +
                       get_percentage_str(self.unweighted_optimal.power_consumption))
            out.append(indent * '  ' + "Weighted w/o alternates: " +
                       get_percentage_str(self.weighted_default.power_consumption))
            out.append(indent * '  ' + "Weighted w/ alternates: " +
                       get_percentage_str(self.weighted_optimal.power_consumption))
            indent -= 1
            out.append(indent * '  ' + "Complexity:")
            indent += 1
            out.append(indent * '  ' + "Unweighted w/o alternates: " +
                       get_percentage_str(self.unweighted_default.complexity))
            out.append(indent * '  ' + "Unweighted w/ alternates: " +
                       get_percentage_str(self.unweighted_optimal.complexity))
            out.append(indent * '  ' + "Weighted w/o alternates: " +
                       get_percentage_str(self.weighted_default.complexity))
            out.append(indent * '  ' + "Weighted w/ alternates: " +
                       get_percentage_str(self.weighted_optimal.complexity))
            return '\n'.join(out)

        def __str__(self):
            return self.to_string()

    class RelateRecipeStats:
        def __init__(self, recipe, product_item, recipe_stats, recipe_comp_stats):
            self.recipe = recipe
            self.product_item = product_item
            self.recipe_stats = recipe_stats
            self.recipe_comp_stats = recipe_comp_stats

        def __str__(self):
            out = []
            out.append("To make 1 " + self.product_item.human_readable_name() +
                       " with " + self.recipe.human_readable_name())
            out.append(str(self.recipe_stats.base))
            out.append("")
            out.append("Relative Statistics:")
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
                out.append("To make 1 " + product_item.human_readable_name() +
                           " with " + self.base_recipe.human_readable_name())
                out.append(str(normalized_stats.base))
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
            self.scaled_production_stats(stats.unweighted_default, scalar),
            self.scaled_production_stats(stats.unweighted_optimal, scalar),
            self.scaled_production_stats(stats.weighted_default, scalar),
            self.scaled_production_stats(stats.weighted_optimal, scalar),
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

        print(result)

        inputs.update(result.inputs())

        return self.ProductionStats(
            inputs,
            -result.net_power() + recipe.crafter().power_consumption(),
            len(result.recipes()) + len(inputs) + 1
        )

    async def compute_recipe_stats(self, recipe):
        base_stats = self.get_base_stats(recipe)
        unweighted_default_stats = await self.compute_production_stats(recipe, False, False)
        unweighted_optimal_stats = await self.compute_production_stats(recipe, False, True)
        weighted_default_stats = await self.compute_production_stats(recipe, True, False)
        weighted_optimal_stats = await self.compute_production_stats(recipe, True, True)
        return self.RecipeStats(
            base_stats,
            unweighted_default_stats,
            unweighted_optimal_stats,
            weighted_default_stats,
            weighted_optimal_stats
        )

    async def compare(self, query):

        # For the base and each related recipe we want to run an optimization query to produce
        # one of the product. We also need to disable all related recipes to force this candidate
        # to be used.

        # The goal is to get, for each candidate recipe, the ingredients, any other products,
        # the raw resources, total power, physical space required, number of steps, etc.

        print("=== Base Stats ===")
        base_stats = await self.compute_recipe_stats(query.base_recipe)
        print(base_stats)

        # product_var -> (product, normalized_base_stats, [related_recipe_stats])
        product_stats = {}
        for product in query.base_recipe.products().values():
            print("=== Evaluating for",
                  product.item().human_readable_name(), "product ===")

            print("=== Base Stats Normalized ===")
            base_stats_normalized = self.scaled_recipe_stats(
                base_stats, 1 / product.minute_rate())
            print(base_stats_normalized)

            related_recipe_stats = []
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
                related_stats = await self.compute_recipe_stats(related_recipe)
                related_stats_normalized = self.scaled_recipe_stats(
                    related_stats, 1 / related_product_minute_rate)
                print(related_stats_normalized)
                # related_recipe_stats[related_recipe.var()] = (
                #     related_recipe, related_stats_normalized)
                comp_stats = self.RecipeCompStats(
                    base_stats_normalized, related_stats_normalized)
                related_recipe_stats.append(self.RelateRecipeStats(
                    related_recipe, product.item(), related_stats_normalized, comp_stats))

            product_stats[product.item().var()] = (
                product.item(), base_stats_normalized, related_recipe_stats
            )

            recipe_comparison_stats = self.RecipeComparison(
                query.base_recipe, product_stats)
            print()
            print()
            print(recipe_comparison_stats)

        return RecipeCompareResult("compare result")
