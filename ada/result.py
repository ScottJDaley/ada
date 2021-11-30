from discord import Embed
from tabulate import tabulate
import math
import ada.emoji
from ada.result_message import ResultMessage
from ada.breadcrumbs import Breadcrumbs
from ada.item import Item
from ada.recipe_comparer import RecipeComparison
from typing import List


class HelpResult:
    def __str__(self) -> str:
        return """
ADA is a bot for the videogame Satisfactory.

ADA can be used to get information about items,
buildings, and recipes. ADA can also be used to
calculate an optimal production chain. Here are
some examples of queries that ADA supports:

```
ada iron rod
```
```
ada recipes for iron rod
```
```
ada recipes for refineries
```

```
ada produce 60 iron rods
```
```
ada produce 60 iron rod from ? iron ore
```
```
ada produce ? iron rods from 60 iron ore
```
```
ada produce ? power from 240 crude oil with only
    fuel generators
```
```
ada produce 60 modular frames without refineries
```

For more information and examples, see [the GitHub page](https://github.com/ScottJDaley/ada).

If you have any questions or concerns, please join the [ADA Bot Support Server](https://discord.gg/UnFkv4wDYJ).
"""

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        message = ResultMessage()
        message.embed = Embed(title="Help")
        message.embed.description = str(self)
        message.content = str(breadcrumbs)
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        return None


class ErrorResult:
    def __init__(self, msg: str) -> None:
        self.__msg = msg

    def __str__(self):
        return self.__msg

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        message = ResultMessage()
        message.embed = Embed(title="Error")
        message.embed.description = self.__msg
        message.content = str(breadcrumbs)
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        return None


class InfoResult:
    num_on_page = 9

    def __init__(self, vars_: List[Item], raw_query: str) -> None:
        self._vars = sorted(vars_, key=lambda var_: var_.human_readable_name())
        self._raw_query = raw_query
        self._add_reaction_selectors = False

    def __str__(self):
        if len(self._vars) == 1:
            return self._vars[0].details()
        var_names = [var.human_readable_name() for var in self._vars]
        var_names.sort()
        return "\n".join(var_names)

    def _num_pages(self):
        return math.ceil(len(self._vars) / InfoResult.num_on_page)

    def _footer(self, page):
        return "Page " + str(page) + " of " + str(self._num_pages())

    def _get_var_on_page(self, page, index):
        var_index = (page - 1) * InfoResult.num_on_page + index
        return self._vars[var_index]

    def _get_info_page(self, breadcrumbs):
        var_names = [var.human_readable_name() for var in self._vars]
        start_index = (breadcrumbs.page() - 1) * InfoResult.num_on_page
        last_index = start_index + InfoResult.num_on_page

        vars_on_page = var_names[start_index:last_index]

        out = []
        message = ResultMessage()
        for i, var_ in enumerate(vars_on_page):
            prefix = ""
            if self._add_reaction_selectors:
                prefix = ada.emoji.NUM_EMOJI[i + 1]
                message.reactions.append(prefix)
            out.append("- " + prefix + var_)
        if not self._add_reaction_selectors:
            message.reactions = []
            if breadcrumbs.page() > 1:
                message.reactions.append(ada.emoji.PREVIOUS_PAGE)
            message.reactions.append(ada.emoji.INFO)
            if breadcrumbs.page() < self._num_pages():
                message.reactions.append(ada.emoji.NEXT_PAGE)

        message.embed = Embed(title=f"Found {len(self._vars)} matches:")
        message.embed.description = "\n".join(out)
        message.embed.set_footer(text=self._footer(breadcrumbs.page()))
        message.content = str(breadcrumbs)
        return [message]

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        if len(self._vars) == 0:
            message = ResultMessage()
            message.embed = Embed(title="No matches found")
            message.content = str(breadcrumbs)
            return [message]
        if len(self._vars) > 1:
            return self._get_info_page(breadcrumbs)
        message = ResultMessage()
        message.embed = self._vars[0].embed()
        message.content = str(breadcrumbs)
        message.reactions = [ada.emoji.PREVIOUS_PAGE]
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        query = None
        if emoji == ada.emoji.INFO:
            self._add_reaction_selectors = True
        elif emoji == ada.emoji.PREVIOUS_PAGE and breadcrumbs.has_prev_query():
            breadcrumbs.goto_prev_query()
            query = breadcrumbs.primary_query()
        elif emoji == ada.emoji.NEXT_PAGE and breadcrumbs.page() < self._num_pages():
            breadcrumbs.goto_next_page()
        elif emoji == ada.emoji.PREVIOUS_PAGE and breadcrumbs.page() > 1:
            breadcrumbs.goto_prev_page()
        elif emoji in ada.emoji.NUM_EMOJI:
            index = ada.emoji.NUM_EMOJI.index(emoji) - 1
            selected_var = self._get_var_on_page(breadcrumbs.page(), index)
            query = selected_var.human_readable_name()
            breadcrumbs.add_query(query)
        return query


class RecipeCompareResult:
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

        inputs = {}
        inputs["Recipe"] = recipes
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
        out.append(tabulate(self.__overall_stats, headers="keys", tablefmt="grid"))
        out.append("")
        out.append("Raw Inputs for 1/m " + product_name)
        out.append(tabulate(self.__input_stats, headers="keys", tablefmt="grid"))
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
                tabulate(self.__overall_stats, headers="keys", tablefmt="simple")
            )
        )
        out.append("Raw Inputs for 1/m " + product_name)
        out.append(
            "```\n{}```".format(
                tabulate(self.__input_stats, headers="keys", tablefmt="simple")
            )
        )

        message.content = "{}\n{}".format(str(breadcrumbs), "\n".join(out))
        if len(message.content) > 2000:
            message.content = "Output was too long"
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        return None
