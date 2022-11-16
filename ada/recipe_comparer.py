from typing import Dict, List, Tuple

import tabulate

from ada.breadcrumbs import Breadcrumbs
from ada.db.db import DB
from ada.db.item import Item
from ada.db.recipe import Recipe
from ada.optimizer import OptimizationQuery, Optimizer
from ada.result import Result, ResultMessage


class RecipeCompareQuery:
    def __init__(self, raw_query: str) -> None:
        self.raw_query = raw_query
        self.product_item = None
        self.base_recipe = None
        self.related_recipes = None
        self.include_alternates = False

    def __str__(self):
        return self.raw_query


class ProductionStats:
    def __init__(
        self,
        inputs: Dict[str, Tuple[Item, float]],
        power_consumption: float,
        step_count: int,
    ) -> None:
        self.inputs = inputs
        self.power_consumption = power_consumption
        self.step_count = step_count

    def to_string(self, indent=0):
        out = []
        out.append("")
        out.append(indent * "  " + "INPUTS:")
        indent += 1
        for _, (_input, value) in self.inputs.items():
            out.append(
                indent * "  "
                + _input.human_readable_name()
                + ": "
                + str(round(value, 2))
                + "/m"
            )
        indent -= 1
        out.append(indent * "  " + "POWER CONSUMPTION:")
        indent += 1
        out.append(indent * "  " + str(round(self.power_consumption, 2)) + " MW")
        # out.append("PROCESSING STEPS: ")
        # out.append("  " + str(self.step_count))
        return "\n".join(out)

    def __str__(self):
        return self.to_string()


class ProductionCompStats:
    def __init__(
        self,
        base_production_stats: ProductionStats,
        comp_production_stats: ProductionStats,
        weighted: bool,
    ) -> None:

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
            "resource:nitrogen-gas": 4.5,  # TODO
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
                base_resource_total += value * weighted_resources[input_var]
            else:
                base_resource_total += value

        comp_resources_total = 0
        for input_var, (_input, value) in comp_production_stats.inputs.items():
            base_value = None
            if input_var in base_production_stats.inputs:
                _, base_value = base_production_stats.inputs[input_var]
            self.resources[input_var] = (
                _input,
                get_delta_percentage(value, base_value),
            )
            if weighted:
                comp_resources_total += value * weighted_resources[input_var]
            else:
                comp_resources_total += value

        self.resource_requirements = get_delta_percentage(
            comp_resources_total, base_resource_total
        )

        self.power_consumption = get_delta_percentage(
            comp_production_stats.power_consumption,
            base_production_stats.power_consumption,
        )

        self.complexity = get_delta_percentage(
            comp_production_stats.step_count, base_production_stats.step_count
        )


class RecipeStats:
    def __init__(
        self,
        base: ProductionStats,
        unweighted_stats: ProductionStats,
        weighted_stats: ProductionStats,
    ) -> None:
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
        return "\n".join(out)


class RecipeCompStats:
    def __init__(self, base_stats: RecipeStats, comp_stats: RecipeStats) -> None:
        self.unweighted_comp_stats = ProductionCompStats(
            base_stats.unweighted_stats, comp_stats.unweighted_stats, False
        )
        self.weighted_comp_stats = ProductionCompStats(
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
        out.append(indent * "  " + "Inputs:")
        indent += 1
        # out.append(indent * '  ' + "Unweighted w/o alternates:")
        # indent += 1
        for _, (
            resource,
            percentage,
        ) in self.unweighted_comp_stats.resources.items():
            out.append(
                indent * "  "
                + resource.human_readable_name()
                + ": "
                + get_percentage_str(percentage)
            )
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
        out.append(indent * "  " + "Total Resource Requirements:")
        indent += 1
        out.append(
            indent * "  "
            + "Unweighted: "
            + get_percentage_str(self.unweighted_comp_stats.resource_requirements)
        )
        out.append(
            indent * "  "
            + "Weighted: "
            + get_percentage_str(self.weighted_comp_stats.resource_requirements)
        )
        indent -= 1
        out.append(
            indent * "  "
            + "Power Consumption: "
            + get_percentage_str(self.unweighted_comp_stats.power_consumption)
        )
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
        out.append(
            indent * "  "
            + "Complexity: "
            + get_percentage_str(self.unweighted_comp_stats.complexity)
        )
        # indent += 1
        # out.append(indent * '  ' + "Unweighted w/o alternates: " +
        #            get_percentage_str(self.unweighted_comp_stats.complexity))
        # out.append(indent * '  ' + "Unweighted w/ alternates: " +
        #            get_percentage_str(self.unweighted_optimal.complexity))
        # out.append(indent * '  ' + "Weighted w/o alternates: " +
        #            get_percentage_str(self.weighted_default.complexity))
        # out.append(indent * '  ' + "Weighted w/ alternates: " +
        #            get_percentage_str(self.weighted_optimal.complexity))
        return "\n".join(out)

    def __str__(self):
        return self.to_string()


class RelatedRecipeStats:
    def __init__(
        self,
        recipe: Recipe,
        product_item: Item,
        recipe_stats: RecipeStats,
        recipe_comp_stats: RecipeCompStats,
    ) -> None:
        self.recipe = recipe
        self.product_item = product_item
        self.recipe_stats = recipe_stats
        self.recipe_comp_stats = recipe_comp_stats

    def __str__(self):
        out = []
        out.append(
            "To make 1 "
            + self.product_item.human_readable_name()
            + " with "
            + self.recipe.human_readable_name()
        )
        out.append(str(self.recipe_stats.base))
        out.append("")
        out.append("Relative Statistics:")
        out.append(self.recipe_comp_stats.to_string(1))
        return "\n".join(out)


class RecipeComparison:
    def __init__(
        self,
        query: RecipeCompareQuery,
        base_stats_normalized: RecipeStats,
        related_recipe_stats: List[RelatedRecipeStats],
    ) -> None:
        self.query = query
        self.base_stats_normalized = base_stats_normalized
        self.related_recipe_stats = related_recipe_stats

    def __str__(self):
        out = []
        out.append(
            "=== Comparing Recipes for "
            + self.query.product_item.human_readable_name()
            + " ==="
        )
        out.append("")
        out.append(
            "To make 1 "
            + self.query.product_item.human_readable_name()
            + " with "
            + self.query.base_recipe.human_readable_name()
        )
        out.append(str(self.base_stats_normalized.base))
        for related_stats in self.related_recipe_stats:
            out.append("")
            out.append(str(related_stats))
        return "\n".join(out)


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

        query = OptimizationQuery("")
        query.maximize_objective = False
        if weighted:
            query.objective_coefficients = {"weighted-resources": -1}
        else:
            query.objective_coefficients = {"unweighted-resources": -1}
        for ingredient_var, ingredient in recipe.ingredients().items():
            if ingredient.item().is_resource():
                inputs[ingredient_var] = (ingredient.item(), ingredient.minute_rate())
            else:
                query.eq_constraints[ingredient_var] = ingredient.minute_rate()

        if include_alternates:
            query.ge_constraints["alternate-recipes"] = 0

        result = await self.__opt.optimize(query)

        inputs.update(result.inputs())

        return ProductionStats(
            inputs,
            -result.net_power() + recipe.crafter().power_consumption(),
            len(result.recipes()) + len(inputs) + 1,
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

    async def compare(self, query: RecipeCompareQuery) -> RecipeComparison:

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


class RecipeCompareResult(Result):
    def __init__(self, stats: RecipeComparison) -> None:
        self.__stats = stats

        def get_percentage_str(percentage):
            if isinstance(percentage, str):
                return percentage
            percentage_string = str(int(round(percentage, 0)))
            if percentage > 0:
                percentage_string = "+" + percentage_string
            return percentage_string + "%"

        recipes = []
        unweighted = []
        weighted = []
        power = []
        complexity = []

        recipes.append(stats.query.base_recipe.human_readable_name())
        unweighted.append("")
        weighted.append("")
        power.append("")
        complexity.append("")

        for related_stats in stats.related_recipe_stats:
            recipes.append(related_stats.recipe.human_readable_name())
            unweighted.append(
                get_percentage_str(
                    related_stats.recipe_comp_stats.unweighted_comp_stats.resource_requirements
                )
            )
            weighted.append(
                get_percentage_str(
                    related_stats.recipe_comp_stats.weighted_comp_stats.resource_requirements
                )
            )
            power.append(
                get_percentage_str(
                    related_stats.recipe_comp_stats.unweighted_comp_stats.power_consumption
                )
            )
            complexity.append(
                get_percentage_str(
                    related_stats.recipe_comp_stats.unweighted_comp_stats.complexity
                )
            )

        self.__overall_stats = {
            "Recipe": recipes,
            "Unweighted\nResources": unweighted,
            "Weighted\nResources": weighted,
            "Power\nConsumption": power,
            "Complexity": complexity,
        }

        # Find all possible inputs.

        input_vars = {}

        for (
            _input,
            value,
        ) in stats.base_stats_normalized.unweighted_stats.inputs.values():
            input_vars[_input.var()] = _input.human_readable_name()
        for related_stats in stats.related_recipe_stats:
            for (
                _input,
                value,
            ) in related_stats.recipe_stats.unweighted_stats.inputs.values():
                input_vars[_input.var()] = _input.human_readable_name()

        inputs = {"Recipe": recipes}
        for input_var, input_name in input_vars.items():
            if input_var in stats.base_stats_normalized.unweighted_stats.inputs:
                _input, value = stats.base_stats_normalized.unweighted_stats.inputs[
                    input_var
                ]
                inputs[input_name] = [str(round(value, 2))]
            else:
                inputs[input_name] = [""]
            for related_stats in stats.related_recipe_stats:
                if input_var in related_stats.recipe_stats.unweighted_stats.inputs:
                    _input, value = related_stats.recipe_stats.unweighted_stats.inputs[
                        input_var
                    ]
                    (
                        resource,
                        percentage,
                    ) = related_stats.recipe_comp_stats.unweighted_comp_stats.resources[
                        input_var
                    ]
                    percentage_str = get_percentage_str(percentage)
                    inputs[input_name].append(
                        "{}/m ({})".format(round(value, 2), percentage_str)
                    )
                else:
                    inputs[input_name].append("")

        raw_power = []
        power_value = stats.base_stats_normalized.unweighted_stats.power_consumption
        raw_power.append("{} MW".format(round(power_value, 1)))
        for related_stats in stats.related_recipe_stats:
            power_value = related_stats.recipe_stats.unweighted_stats.power_consumption
            power_percentage = (
                related_stats.recipe_comp_stats.unweighted_comp_stats.power_consumption
            )
            percentage_str = get_percentage_str(power_percentage)
            raw_power.append("{} MW ({})".format(round(power_value, 1), percentage_str))

        inputs["Power"] = raw_power

        self.__input_stats = inputs

    def __str__(self) -> str:
        # === OVERALL STATS ===
        #                               | Unweighted | Weighted  | Power       |            |
        #  Recipe                       | Resources  | Resources | Consumption | Complexity |
        #  -----------------------------|------------|-----------|-------------|------------|
        #  Recipe: Iron Rod             |            |           |             |            |
        #  -----------------------------|------------|-----------|-------------|------------|
        #  Recipe: Alternate: Steel Rod |  -50%      |  -1.25%   |  -56%       |  +33%      |
        #
        # === RAW INPUTS ===
        #                               | Iron          |              |             |            |
        #  Recipe                       | Ore           | Coal         |             |   Power    |
        #  -----------------------------|---------------|--------------|-------------|------------|
        #  Recipe: Iron Rod             | 0.75/m        |              |             |   0.27 MW  |
        #  -----------------------------|---------------|--------------|-------------|------------|
        #  Recipe: Alternate: Steel Rod | 0.25/m (-75%) | 0.45/m (NEW) |             |   1.2 MW   |
        product_name = self.__stats.query.product_item.human_readable_name()

        out = []
        out.append("All recipes that produce " + product_name)
        out.append(tabulate.tabulate(self.__overall_stats, headers="keys", tablefmt="grid"))
        out.append("")
        out.append("Raw Inputs for 1/m " + product_name)
        out.append(tabulate.tabulate(self.__input_stats, headers="keys", tablefmt="grid"))
        return "\n".join(out)

        # return str(self.__stats)

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        message = ResultMessage()
        # message.embed = Embed(title="Error")
        # message.embed.description = "hello"  # "```{}```".format(str(self))

        product_name = self.__stats.query.product_item.human_readable_name()

        out = []
        out.append("All recipes that produce " + product_name)
        out.append(
            "```\n{}```".format(
                tabulate.tabulate(self.__overall_stats, headers="keys", tablefmt="simple")
            )
        )
        out.append("Raw Inputs for 1/m " + product_name)
        out.append(
            "```\n{}```".format(
                tabulate.tabulate(self.__input_stats, headers="keys", tablefmt="simple")
            )
        )

        message.content = "{}\n{}".format(str(breadcrumbs), "\n".join(out))
        if len(message.content) > 2000:
            message.content = "Output was too long"
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        return None
