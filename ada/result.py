import pulp
from graphviz import Digraph
from discord import Embed, File
import math

import ada.emoji
from ada.result_message import ResultMessage
from ada.breadcrumbs import Breadcrumbs


class HelpResult:
    def __str__(self):
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
"""

    def message(self, breadcrumbs):
        message = ResultMessage()
        message.embed = Embed(title="Help")
        message.embed.description = str(self)
        message.content = str(breadcrumbs)
        return message

    def handle_reaction(self, emoji, breadcrumbs):
        return None


class ErrorResult:
    def __init__(self, msg):
        self.__msg = msg

    def __str__(self):
        return self.__msg

    def message(self, breadcrumbs):
        message = ResultMessage()
        message.embed = Embed(title="Error")
        message.embed.description = self.__msg
        message.content = str(breadcrumbs)
        return message

    def handle_reaction(self, emoji, breadcrumbs):
        return None


class InfoResult:
    num_on_page = 9

    def __init__(self, vars_, raw_query):
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
                prefix = ada.emoji.NUM_EMOJI[i+1]
                message.reactions.append(prefix)
            out.append("- " + prefix + var_)
        if not self._add_reaction_selectors:
            message.reactions = []
            if breadcrumbs.page() > 1:
                message.reactions.append(ada.emoji.PREVIOUS_PAGE)
            message.reactions.append(ada.emoji.INFO)
            if breadcrumbs.page() < self._num_pages():
                message.reactions.append(ada.emoji.NEXT_PAGE)

        message.embed = Embed(
            title="Found " + str(len(self._vars)) + " matches:")
        message.embed.description = "\n".join(out)
        message.embed.set_footer(text=self._footer(breadcrumbs.page()))
        message.content = str(breadcrumbs)
        return message

    def message(self, breadcrumbs):
        if len(self._vars) == 0:
            message = ResultMessage()
            message.embed = Embed(title="No matches found")
            message.content = str(breadcrumbs)
            return message
        if len(self._vars) > 1:
            return self._get_info_page(breadcrumbs)
        message = ResultMessage()
        message.embed = self._vars[0].embed()
        message.content = str(breadcrumbs)
        message.reactions = [ada.emoji.PREVIOUS_PAGE]
        return message

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


class OptimizationResult:
    def __init__(self, db, vars_, prob, status, query):
        self.__db = db
        self.__prob = prob
        self.__vars = vars_
        self.__status = status
        self.__query = query
        # Dictionaries from var -> (obj, value)
        # TODO: Use these in the functions below
        self.__inputs = {
            item.var(): (item, -self.__get_value(item.var()))
            for item in self.__db.items().values()
            if self.__has_value(item.var()) and self.__get_value(item.var()) < 0
        }
        self.__outputs = {
            item.var(): (item, self.__get_value(item.var()))
            for item in self.__db.items().values()
            if self.__has_value(item.var()) and self.__get_value(item.var()) > 0
        }
        self.__recipes = {
            recipe.var(): (recipe, self.__get_value(recipe.var()))
            for recipe in self.__db.recipes().values()
            if self.__has_value(recipe.var())
        }
        self.__crafters = {
            crafter.var(): (crafter, self.__get_value(crafter.var()))
            for crafter in self.__db.crafters().values()
            if self.__has_value(crafter.var())
        }
        self.__generators = {
            generator.var(): (generator, self.__get_value(generator.var()))
            for generator in self.__db.generators().values()
            if self.__has_value(generator.var())
        }
        self.__net_power = self.__get_value(
            "power") if self.__has_value("power") else 0

    def inputs(self):
        return self.__inputs

    def outputs(self):
        return self.__outputs

    def recipes(self):
        return self.__recipes

    def crafters(self):
        return self.__crafters

    def generators(self):
        return self.__generators

    def net_power(self):
        return self.__net_power

    def __has_value(self, var):
        return self.__vars[var].value() and self.__vars[var].value() != 0

    def __get_value(self, var):
        return self.__vars[var].value()

    def __get_vars(self, objs, check_value=lambda val: True, suffix=""):
        out = []
        for obj in objs:
            var = obj.var()
            if self.__has_value(var) and check_value(self.__get_value(var)):
                out.append(obj.human_readable_name() +
                           ": " + str(round(abs(self.__get_value(var)), 2)) + suffix)
        return out

    def __get_section(self, title, objs, check_value=lambda val: True, suffix=""):
        out = []
        out.append(title)
        vars_ = self.__get_vars(objs, check_value=check_value, suffix=suffix)
        if len(vars_) == 0:
            return []
        out = []
        out.append(title)
        out.extend(vars_)
        out.append("")
        return out

    def __string_solution(self):
        out = []
        out.append(str(self.__query))
        out.append("=== OPTIMAL SOLUTION FOUND ===\n")
        out.extend(self.__get_section(
            "INPUT", self.__db.items().values(), check_value=lambda val: val < 0, suffix="/m"))
        out.extend(self.__get_section(
            "OUTPUT", self.__db.items().values(), check_value=lambda val: val > 0, suffix="/m"))
        # out.extend(self.__get_section("INPUT", [item.input() for item in self.__db.items().values()]))
        # out.extend(self.__get_section("OUTPUT", [item.output() for item in self.__db.items().values()]))
        out.extend(self.__get_section("RECIPES", self.__db.recipes().values()))
        out.extend(self.__get_section(
            "CRAFTERS", self.__db.crafters().values()))
        out.extend(self.__get_section(
            "GENERATORS", self.__db.generators().values()))
        out.append("NET POWER")
        net_power = 0
        if self.__has_value("power"):
            net_power = self.__get_value("power")
        out.append(str(net_power) + " MW")
        out.append("")
        out.append("OBJECTIVE VALUE")
        out.append(str(self.__prob.objective.value()))
        return '\n'.join(out)

    def __str__(self):
        if self.__status is pulp.LpStatusNotSolved:
            return "No solution has been found."
        if self.__status is pulp.LpStatusUndefined:
            return "No solution has been found."
        if self.__status is pulp.LpStatusInfeasible:
            return "Solution is infeasible, try removing a constraint or allowing a byproduct (e.g. rubber >= 0)"
        if self.__status is pulp.LpStatusUnbounded:
            return "Solution is unbounded, try adding a constraint or replacing '?' with a concrete value (e.g. 1000)"
        return self.__string_solution()

    def __solution_message(self, breadcrumbs):
        message = ResultMessage()
        message.embed = Embed(title="Optimization Query")
        # We don't include the parsed query in case this puts the embed over the character limit
        # message.embed.description = str(self.__query)
        message.embed.description = " "
        inputs = self.__get_vars(
            self.__db.items().values(), check_value=lambda val: val < 0, suffix="/m")
        if len(inputs) > 0:
            message.embed.add_field(
                name="Inputs", value="\n".join(inputs), inline=True)
        outputs = self.__get_vars(
            self.__db.items().values(), check_value=lambda val: val > 0, suffix="/m")
        if len(outputs) > 0:
            message.embed.add_field(
                name="Outputs", value="\n".join(outputs), inline=True)
        recipes = self.__get_vars(self.__db.recipes().values())
        if len(recipes) > 0:
            message.embed.add_field(
                name="Recipes", value="\n".join(recipes), inline=False)
        buildings = self.__get_vars(self.__db.crafters().values())
        buildings.extend(self.__get_vars(self.__db.generators().values()))
        if len(buildings) > 0:
            message.embed.add_field(name="Buildings", value="\n".join(
                buildings), inline=True)

        filename = 'output.gv'
        filepath = 'output/' + filename
        self.generate_graph_viz(filepath)
        file = File(filepath + '.png')
        # The image already shows up from the attached file, so no need to place it in the embed as well.
        # message.embed.set_image(url="attachment://" + filename + ".png")
        message.file = file
        message.content = breadcrumbs
        return message

    def message(self, breadcrumbs):
        if self.__status is pulp.LpStatusOptimal:
            return self.__solution_message(breadcrumbs)
        message = ResultMessage()
        message.embed = Embed(title=str(self))
        message.content = str(breadcrumbs)
        return message

    def handle_reaction(self, emoji, breadcrumbs):
        return None

    def __add_nodes(self, s, objs):
        for obj in objs:
            var = obj.var()
            if not self.__has_value(var):
                continue
            amount = self.__get_value(var)
            s.node(obj.viz_name(), obj.viz_label(amount), shape="plaintext")

    def __has_non_zero_var(self):
        for var in self.__vars:
            if self.__has_value(var):
                return True
        return False

    def has_solution(self):
        return self.__status is pulp.LpStatusOptimal and self.__has_non_zero_var()

    def __power_viz_label(self, output, net):
        color = "moccasin" if net < 0 else "lightblue"
        out = '<'
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        if output > 0:
            out += '<TR>'
            out += '<TD COLSPAN="2" BGCOLOR="' + color + '">Power Output</TD>'
            out += '<TD>' + str(round(output, 2)) + ' MW</TD>'
            out += '</TR>'
        out += '<TR>'
        out += '<TD COLSPAN="2" BGCOLOR="' + color + '">Net Power</TD>'
        out += '<TD>' + str(round(net, 2)) + ' MW</TD>'
        out += '</TR>'
        out += '</TABLE>>'
        return out

    def generate_graph_viz(self, filename):
        s = Digraph('structs', format='png', filename=filename,
                    node_attr={'shape': 'record'})

        sources = {}  # item => {source => amount}
        sinks = {}  # item => {sink => amount}

        def add_to_target(item_var, targets, target, amount):
            if item_var not in targets:
                targets[item_var] = {}
            targets[item_var][target] = amount

        # items
        self.__add_nodes(s, self.__db.items().values())
        for item in self.__db.items().values():
            if not self.__has_value(item.var()):
                continue
            amount = self.__get_value(item.var())
            target = sources if amount < 0 else sinks
            add_to_target(item.var(), target, item.viz_name(),
                          self.__get_value(item.var()))
        # recipes
        self.__add_nodes(s, self.__db.recipes().values())
        for recipe in self.__db.recipes().values():
            if not self.__has_value(recipe.var()):
                continue
            recipe_amount = self.__get_value(recipe.var())
            for item_var, ingredient in recipe.ingredients().items():
                ingredient_amount = recipe_amount * ingredient.minute_rate()
                add_to_target(item_var, sinks, recipe.viz_name(),
                              ingredient_amount)
            for item_var, product in recipe.products().items():
                product_amount = recipe_amount * product.minute_rate()
                add_to_target(item_var, sources,
                              recipe.viz_name(), product_amount)
        # power
        power_output = 0
        net_power = 0
        if self.__has_value("power"):
            net_power = self.__get_value("power")

        def get_power_edge_label(power_production):
            return str(round(power_production, 2)) + ' MW'

        # power recipes
        self.__add_nodes(s, self.__db.power_recipes().values())
        for power_recipe in self.__db.power_recipes().values():
            if not self.__has_value(power_recipe.var()):
                continue
            fuel_item = power_recipe.fuel_item()
            fuel_amount = self.__get_value(
                power_recipe.var()) * power_recipe.fuel_minute_rate()
            add_to_target(fuel_item.var(), sinks,
                          power_recipe.viz_name(), fuel_amount)
            power_production = self.__get_value(
                power_recipe.var()) * power_recipe.power_production()
            power_output += power_production
            s.edge(power_recipe.viz_name(), "power",
                   label=get_power_edge_label(power_production))

        s.node("power", self.__power_viz_label(
            power_output, net_power), shape="plaintext")

        def get_edge_label(item, amount):
            return str(round(amount, 2)) + '/m\n' + item

        # Connect each source to all sinks of that item
        for item_var, item_sources in sources.items():
            item = self.__db.items()[item_var]
            if item_var not in sinks:
                print("Could not find", item_var, "in sinks")
                continue
            for source, source_amount in item_sources.items():
                total_sink_amount = 0
                for _, sink_amount in sinks[item_var].items():
                    total_sink_amount += sink_amount
                multiplier = source_amount / total_sink_amount
                for sink, sink_amount in sinks[item_var].items():
                    s.edge(source, sink, label=get_edge_label(
                        item.human_readable_name(), multiplier * sink_amount))

        s.render()


class RecipeCompareResult:
    def __init__(self, msg):
        self.__msg = msg

    def __str__(self):

        # We want something like this:
        # Comparing Recipe: Iron Rod
        #
        # Recipe: Alternate: Steel Rod
        #   To make 1 Iron Rod per minute:
        #     INPUTS:
        #       Steel Ingot: 0.25/m
        #     POWER CONSUMPTION:
        #       0.083 MW
        #
        #   Compared to Recipe: Iron Rod
        #     Resource Requirements:
        #       Unweighted w/o alternates:
        #         Coal: +100%
        #         Iron Ore: -20%
        #       Unweighted w/ alternates:
        #         Water: -67.5%
        #         Iron Ore: +11%%
        #         Crude Oil: + 100%
        #       Weighted w/o alternates:
        #         Water: -67.5%
        #         Iron Ore: +11%%
        #         Crude Oil: + 100%
        #       Weighted w/ alternates:
        #         Water: -67.5%
        #         Iron Ore: +11%%
        #         Crude Oil: + 100%
        #     Productivity:
        #       Unweighted w/o alternates: +25%
        #       Unweighted w/ alternates:  +55%
        #       Weighted w/o alternates:   +33%
        #       Weighted w/ alternates:    +60%
        #     Power Consumption:
        #       Unweighted w/o alternates: +25%
        #       Unweighted w/ alternates:  +55%
        #       Weighted w/o alternates:   +33%
        #       Weighted w/ alternates:    +60%
        #     Complexity:
        #       Unweighted w/o alternates: +25%
        #       Unweighted w/ alternates:  +55%
        #       Weighted w/o alternates:   +33%
        #       Weighted w/ alternates:    +60%

        # TODO: Actually, let's do something like this instead

        # Recipe: Alternate: Steel Rod
        #   Inputs:
        #     Iron Ore: -20%
        #     Coal: +100%
        #     Water: +67%
        #     Crude Oil: +100%
        #   total Resource Requirements:
        #     unweighted: -25%
        #     weighted: -40%
        #   Power Consumption: -25%
        #   Complexity: -25%

        return self.__msg

    def message(self, breadcrumbs):
        message = ResultMessage()
        message.embed = Embed(title="Error")
        message.embed.description = self.__msg
        message.content = str(breadcrumbs)
        return message

    def handle_reaction(self, emoji, breadcrumbs):
        return None
