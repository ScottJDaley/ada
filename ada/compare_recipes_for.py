import tabulate

from .db.item import Item
from .db.recipe import Recipe
from .query import Query
from .result import Result


class CompareRecipesForQuery(Query):
    def __init__(self) -> None:
        self.product_item: Item | None = None
        self.base_recipe = None
        self.related_recipes = None
        self.include_alternates = False

    def __str__(self):
        return f"compare recipes for {self.product_item.var()}" \
               f"{' with alternate recipes' if self.include_alternates else ''}"


class ProductionStats:
    def __init__(
            self,
            inputs: dict[str, tuple[Item, float]],
            power_consumption: float,
            step_count: int,
    ) -> None:
        self.inputs = inputs
        self.power_consumption = power_consumption
        self.step_count = step_count

    def to_string(self, indent=0):
        out = [
            "",
            indent * "  " + "INPUTS:"
        ]
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
            "item:water": 0,
            "item:iron-ore": 1,
            "item:copper-ore": 3.29,
            "item:limestone": 1.47,
            "item:coal": 2.95,
            "item:crude-oil": 4.31,
            "item:bauxite": 8.48,
            "item:caterium-ore": 6.36,
            "item:uranium": 46.67,
            "item:raw-quartz": 6.36,
            "item:sulfur": 13.33,
            "item:nitrogen-gas": 4.5,  # TODO
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
        out = [
            "",
            "Base:",
            str(self.base),
            "",
            "Unweighted",
            str(self.unweighted_stats),
            "",
            "Weighted",
            str(self.weighted_stats)
        ]
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

        out = [indent * "  " + "Inputs:"]
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
        out = [
            "To make 1 " + self.product_item.human_readable_name() + " with " + self.recipe.human_readable_name(),
            str(self.recipe_stats.base),
            "",
            "Relative Statistics:",
            self.recipe_comp_stats.to_string(1)
        ]
        return "\n".join(out)


class RecipeComparison:
    def __init__(
            self,
            query: CompareRecipesForQuery,
            base_stats_normalized: RecipeStats,
            related_recipe_stats: list[RelatedRecipeStats],
    ) -> None:
        self.query: CompareRecipesForQuery = query
        self.base_stats_normalized = base_stats_normalized
        self.related_recipe_stats = related_recipe_stats

    def __str__(self):
        out = [
            "=== Comparing Recipes for " + self.query.product_item.human_readable_name() + " ===",
            "",
            "To make 1 " + self.query.product_item.human_readable_name() + " with "
            + self.query.base_recipe.human_readable_name(),
            str(self.base_stats_normalized.base)
        ]
        for related_stats in self.related_recipe_stats:
            out.append("")
            out.append(str(related_stats))
        return "\n".join(out)


class CompareRecipesForResult(Result):
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

        for (_input, value) in stats.base_stats_normalized.unweighted_stats.inputs.values():
            input_vars[_input.var()] = _input.human_readable_name()
        for related_stats in stats.related_recipe_stats:
            for (_input, value) in related_stats.recipe_stats.unweighted_stats.inputs.values():
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

        out = [
            "All recipes that produce " + product_name,
            tabulate.tabulate(self.__overall_stats, headers="keys", tablefmt="grid"),
            "",
            "Raw Inputs for 1/m " + product_name,
            tabulate.tabulate(self.__input_stats, headers="keys", tablefmt="grid")
        ]
        return "\n".join(out)

        # return str(self.__stats)

    def stats(self):
        return self.__stats

    def overall_stats(self):
        return self.__overall_stats

    def input_stats(self):
        return self.__input_stats
