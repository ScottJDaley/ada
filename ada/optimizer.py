import os
from typing import Dict

import pulp
from graphviz import Digraph
from pulp.constants import (
    LpStatusInfeasible,
    LpStatusNotSolved,
    LpStatusOptimal,
    LpStatusUnbounded,
    LpStatusUndefined,
)
from pulp.pulp import LpProblem, LpVariable

from .db.db import DB
from .optimization_query import AmountValue, AnyValue, MaximizeValue, OptimizationQuery, Output
from .optimization_result_data import OptimizationResultData
from .result import Result

EPSILON = 0.000001


class OptimizationResult(Result):
    def __init__(
            self,
            db: DB,
            vars_: Dict[str, LpVariable],
            prob: LpProblem,
            status: int,
            query: OptimizationQuery,
    ) -> None:
        self.__db = db
        self.__prob = prob
        self.__vars = vars_
        self.__status = status
        self.__query = query
        # Dictionaries from var -> (obj, value)
        # TODO: Use these in the functions below
        inputs = {
            item.var(): (item, -self.__get_value(item.var()))
            for item in self.__db.items().values()
            if self.__has_value(item.var()) and self.__get_value(item.var()) < 0
        }
        outputs = {
            item.var(): (item, self.__get_value(item.var()))
            for item in self.__db.items().values()
            if self.__has_value(item.var()) and self.__get_value(item.var()) > 0
        }
        recipes = {
            recipe.var(): (recipe, self.__get_value(recipe.var()))
            for recipe in self.__db.recipes().values()
            if self.__has_value(recipe.var())
        }
        crafters = {
            crafter.var(): (crafter, self.__get_value(crafter.var()))
            for crafter in self.__db.crafters().values()
            if self.__has_value(crafter.var())
        }
        generators = {
            generator.var(): (generator, self.__get_value(generator.var()))
            for generator in self.__db.generators().values()
            if self.__has_value(generator.var())
        }
        net_power = self.__get_value("power") if self.__has_value("power") else 0

        self.__result_data = OptimizationResultData(
            inputs=inputs,
            outputs=outputs,
            recipes=recipes,
            crafters=crafters,
            generators=generators,
            net_power=net_power
        )

    def result_data(self) -> OptimizationResultData:
        return self.__result_data

    def success(self):
        return self.__status is LpStatusOptimal

    def query(self):
        return self.__query

    def __has_value(self, var):
        return (
                self.__vars[var].value()
                and abs(self.__vars[var].value()) > EPSILON
        )

    def __get_value(self, var):
        return self.__vars[var].value()

    def __get_vars(self, objs, check_value=lambda val: True, suffix=""):
        out = []
        for obj in objs:
            var = obj.var()
            if self.__has_value(var) and check_value(self.__get_value(var)):
                out.append(
                    obj.human_readable_name()
                    + ": "
                    + str(round(abs(self.__get_value(var)), 2))
                    + suffix
                )
        return out

    def __get_section(self, title, objs, check_value=lambda val: True, suffix=""):
        out = [title]
        vars_ = self.__get_vars(objs, check_value=check_value, suffix=suffix)
        if len(vars_) == 0:
            return []
        out = [title]
        out.extend(vars_)
        out.append("")
        return out

    def __string_solution(self):
        out = [
            str(self.__query),
            "=== OPTIMAL SOLUTION FOUND ===\n"
        ]
        out.extend(
            self.__get_section(
                "INPUT",
                self.__db.items().values(),
                check_value=lambda val: val < 0,
                suffix="/m",
            )
        )
        out.extend(
            self.__get_section(
                "OUTPUT",
                self.__db.items().values(),
                check_value=lambda val: val > 0,
                suffix="/m",
            )
        )
        # out.extend(self.__get_section("INPUT", [item.input() for item in self.__db.items().values()]))
        # out.extend(self.__get_section("OUTPUT", [item.output() for item in self.__db.items().values()]))
        out.extend(self.__get_section("RECIPES", self.__db.recipes().values()))
        out.extend(self.__get_section("CRAFTERS", self.__db.crafters().values()))
        out.extend(self.__get_section("GENERATORS", self.__db.generators().values()))
        out.append("NET POWER")
        net_power = 0
        if self.__has_value("power"):
            net_power = self.__get_value("power")
        out.append(str(net_power) + " MW")
        out.append("")
        out.append("OBJECTIVE VALUE")
        out.append(str(self.__prob.objective.value()))
        return "\n".join(out)

    def __str__(self) -> str:
        if self.__status is LpStatusNotSolved:
            return "No solution has been found."
        if self.__status is LpStatusUndefined:
            return "No solution has been found."
        if self.__status is LpStatusInfeasible:
            return "Solution is infeasible, try allowing alternate recipes or byproducts in the settings."
        if self.__status is LpStatusUnbounded:
            return "Solution is unbounded, try adding a constraint or replacing '?' with a concrete value (e.g. 1000)"
        return self.__string_solution()

    # def __solution_message(self, breadcrumbs, dispatch: Dispatch):
    #     message = ResultMessage()
    #     message.embed = Embed(title="Optimization Query")
    #
    #     sections = [str(self.__query)]
    #
    #     inputs = self.__get_vars(
    #         self.__db.items().values(), check_value=lambda val: val < 0, suffix="/m"
    #     )
    #     if len(inputs) > 0:
    #         sections.append("**Inputs**\n" + "\n".join(inputs))
    #     outputs = self.__get_vars(
    #         self.__db.items().values(), check_value=lambda val: val > 0, suffix="/m"
    #     )
    #     if len(outputs) > 0:
    #         sections.append("**Outputs**\n" + "\n".join(outputs))
    #     recipes = self.__get_vars(self.__db.recipes().values())
    #     if len(recipes) > 0:
    #         sections.append("**Recipes**\n" + "\n".join(recipes))
    #     buildings = self.__get_vars(self.__db.crafters().values())
    #     buildings.extend(self.__get_vars(self.__db.generators().values()))
    #     if len(buildings) > 0:
    #         sections.append("**Buildings**\n" + "\n".join(buildings))
    #
    #     # descriptions = []
    #     description = ""
    #     for section in sections:
    #         # TODO: Handle this another way
    #         # if len(curr_description) + len(section) >= 4096:
    #         #     descriptions.append(curr_description)
    #         #     curr_description = ""
    #         description += section + "\n\n"
    #     # descriptions.append(curr_description)
    #
    #     message.embed.description = description
    #
    #     filename = "output.gv"
    #     filepath = "output/" + filename
    #     self.generate_graph_viz(filepath)
    #     file = File(filepath + ".png")
    #     # The image already shows up from the attached file, so no need to place it in the embed as well.
    #     message.embed.set_image(url="attachment://" + filename + ".png")
    #     message.file = file
    #     if len(breadcrumbs.current_page().custom_ids()) == 0:
    #         breadcrumbs.current_page().add_custom_id("inputs")
    #     breadcrumbs.current_page().replace_query(str(self.__query))
    #     message.content = str(breadcrumbs)
    #     message.view = views.OptimizationSelectorView.get_view(
    #         breadcrumbs,
    #         dispatch,
    #         self.__result_data,
    #         self.__query
    #     )
    #
    #     # messages = message
    #     #
    #     # if len(descriptions) > 1:
    #     #     for i in range(1, len(descriptions)):
    #     #         next_message = ResultMessage()
    #     #         next_message.embed = Embed()
    #     #         next_message.embed.description = descriptions[i]
    #     #         messages.append(next_message)
    #
    #     return message
    #
    # # def get_optimization_view(self, processor: Processor, custom_id: str) -> discord.ui.View:
    # #     # parts = custom_id.split(".")
    # #     # category = parts[0] if len(parts) > 0 else ""
    # #     # selected = "".join(parts)
    # #     if custom_id == "inputs":
    # #         return InputsCategoryView(processor, self.inputs())
    # #     if custom_id == "outputs":
    # #         return OutputsCategoryView(processor)
    # #     if custom_id == "recipes":
    # #         return RecipesCategoryView(processor)
    # #     if custom_id == "buildings":
    # #         return BuildingsCategoryView(processor)
    # #     if custom_id == "general":
    # #         return GeneralCategoryView(processor)
    # #     return InputsCategoryView(processor, self.inputs())
    #
    # def message(self, breadcrumbs: Breadcrumbs, dispatch: Dispatch) -> ResultMessage:
    #     if self.__status is LpStatusOptimal:
    #         return self.__solution_message(breadcrumbs, dispatch)
    #     message = ResultMessage()
    #     message.embed = Embed(title=str(self))
    #     message.content = str(breadcrumbs)
    #     return message

    def __add_nodes(self, s, objs):
        for obj in objs:
            var = obj.var()
            if not self.__has_value(var):
                continue
            amount = abs(self.__get_value(var))
            s.node(obj.viz_name(), obj.viz_label(amount), shape="plaintext")

    def __has_non_zero_var(self):
        for var in self.__vars:
            if self.__has_value(var):
                return True
        return False

    def has_solution(self) -> bool:
        return self.__status is LpStatusOptimal and self.__has_non_zero_var()

    @staticmethod
    def __power_viz_label(output, net):
        color = "moccasin" if net < 0 else "lightblue"
        out = "<"
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        if output > 0:
            out += "<TR>"
            out += '<TD COLSPAN="2" BGCOLOR="' + color + '">Power Output</TD>'
            out += "<TD>" + str(round(output, 2)) + " MW</TD>"
            out += "</TR>"
        out += "<TR>"
        out += '<TD COLSPAN="2" BGCOLOR="' + color + '">Net Power</TD>'
        out += "<TD>" + str(round(net, 2)) + " MW</TD>"
        out += "</TR>"
        out += "</TABLE>>"
        return out

    def generate_graph_viz(self, filename: str) -> None:
        s = Digraph(
            "structs", format="png", filename=filename, node_attr={"shape": "record"}
        )

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
            add_to_target(
                item.var(), target, item.viz_name(), abs(amount)
            )
        # recipes
        self.__add_nodes(s, self.__db.recipes().values())
        for recipe in self.__db.recipes().values():
            if not self.__has_value(recipe.var()):
                continue
            recipe_amount = -self.__get_value(recipe.var())
            print(f"recipe {recipe.var()}, amount:  {recipe_amount}")
            for item_var, ingredient in recipe.ingredients().items():
                ingredient_amount = recipe_amount * ingredient.minute_rate()
                add_to_target(item_var, sinks, recipe.viz_name(), ingredient_amount)
            for item_var, product in recipe.products().items():
                product_amount = recipe_amount * product.minute_rate()
                add_to_target(item_var, sources, recipe.viz_name(), product_amount)
        # power
        power_output = 0
        net_power = 0
        if self.__has_value("power"):
            net_power = self.__get_value("power")

        def get_power_edge_label(power_production):
            return str(round(power_production, 2)) + " MW"

        # power recipes
        self.__add_nodes(s, self.__db.power_recipes().values())
        for power_recipe in self.__db.power_recipes().values():
            if not self.__has_value(power_recipe.var()):
                continue
            fuel_item = power_recipe.fuel_item()
            fuel_amount = (self.__get_value(power_recipe.var()) * power_recipe.fuel_minute_rate())
            add_to_target(fuel_item.var(), sinks, power_recipe.viz_name(), fuel_amount)
            water_amount = (self.__get_value(power_recipe.var()) * power_recipe.water_minute_rate())
            add_to_target("item:water", sinks, power_recipe.viz_name(), water_amount)
            power_production = -(self.__get_value(power_recipe.var()) * power_recipe.power_production())
            power_output += power_production
            s.edge(
                power_recipe.viz_name(),
                "power",
                label=get_power_edge_label(power_production),
            )

        s.node(
            "power", self.__power_viz_label(power_output, net_power), shape="plaintext"
        )

        def get_edge_label(item, amount):
            return str(round(amount, 2)) + "/m\n" + item

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
                    s.edge(
                        source,
                        sink,
                        label=get_edge_label(
                            item.human_readable_name(), multiplier * sink_amount
                        ),
                    )

        s.render()


POWER = "power"
UNWEIGHTED_RESOURCES = "unweighted-resources"
WEIGHTED_RESOURCES = "weighted-resources"
MEAN_WEIGHTED_RESOURCES = "mean-weighted-resources"
ALTERNATE_RECIPES = "alternate-recipes"


class Optimizer:
    def __init__(self, db: DB) -> None:
        self.__db = db

        self.variable_names = []

        # Create problem variables
        self.__variables = {}
        for recipe in self.__db.recipes():
            self.__variables[recipe] = pulp.LpVariable(recipe, upBound=0)
        for power_recipe in self.__db.power_recipes():
            self.__variables[power_recipe] = pulp.LpVariable(power_recipe, upBound=0)
        for item in self.__db.items().values():
            self.__variables[item.var()] = pulp.LpVariable(item.var())
        for crafter in self.__db.crafters():
            self.__variables[crafter] = pulp.LpVariable(crafter, upBound=0)
        for generator_var, generator in self.__db.generators().items():
            self.__variables[generator_var] = pulp.LpVariable(generator_var, upBound=0)
        self.__variables[POWER] = pulp.LpVariable(POWER)
        self.__variables[UNWEIGHTED_RESOURCES] = pulp.LpVariable(UNWEIGHTED_RESOURCES)
        self.__variables[WEIGHTED_RESOURCES] = pulp.LpVariable(WEIGHTED_RESOURCES)
        self.__variables[MEAN_WEIGHTED_RESOURCES] = pulp.LpVariable(
            MEAN_WEIGHTED_RESOURCES
        )
        self.__variables[ALTERNATE_RECIPES] = pulp.LpVariable(
            ALTERNATE_RECIPES, upBound=0
        )

        self.__equalities = []

        # For each item, create an equality for all inputs and outputs:
        #   products - ingredients = net output
        #   products - ingredients - net output = 0
        for item_var, item in self.__db.items().items():
            var_coeff = {}  # variable => coefficient
            recipes_for_item = self.__db.recipes_for_product(item_var)
            recipes_from_item = self.__db.recipes_for_ingredient(item_var)
            for recipe in recipes_for_item:
                if not recipe.is_craftable_in_building():
                    continue
                var_coeff[self.__variables[recipe.var()]] = recipe.product(
                    item_var
                ).minute_rate()
            for recipe in recipes_from_item:
                if not recipe.is_craftable_in_building():
                    continue
                var_coeff[self.__variables[recipe.var()]] = -recipe.ingredient(
                    item_var
                ).minute_rate()
            if item_var in self.__db.power_recipes_by_fuel():
                power_recipe = self.__db.power_recipes_by_fuel()[item_var]
                var_coeff[
                    self.__variables[power_recipe.var()]
                ] = -power_recipe.fuel_minute_rate()
            if item_var == "item:water":
                for generator in self.__db.generators().values():
                    if generator.requires_water():
                        var_coeff[
                            self.__variables[generator.var()]
                        ] = -generator.water_minute_rate()
            var_coeff[self.__variables[item.var()]] = 1
            # var_coeff[self.__variables[item.output().var()]] = -1
            self.__equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

        # For each type of crafter, create an equality for all recipes that require it
        for crafter_var in self.__db.crafters():
            var_coeff = {}  # variable => coefficient
            for recipe_var, recipe in self.__db.recipes().items():
                if not recipe.is_craftable_in_building():
                    continue
                if recipe.crafter().var() == crafter_var:
                    var_coeff[self.__variables[recipe_var]] = 1
            var_coeff[self.__variables[crafter_var]] = -1
            self.__equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

        # For each type of generator, create an equality for power recipes that require it
        for generator_var in self.__db.generators():
            var_coeff = {}  # variable => coefficient
            for power_recipe_var, power_recipe in self.__db.power_recipes().items():
                if power_recipe.generator().var() == generator_var:
                    var_coeff[self.__variables[power_recipe_var]] = 1
            var_coeff[self.__variables[generator_var]] = -1
            self.__equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

        # Create a single power equality for all recipes and generators
        power_coeff = {}
        for generator_var, generator in self.__db.generators().items():
            power_coeff[self.__variables[generator_var]] = generator.power_production()
        for recipe_var, recipe in self.__db.recipes().items():
            if not recipe.is_craftable_in_building():
                continue
            power_coeff[
                self.__variables[recipe_var]
            ] = -recipe.crafter().power_consumption()
        power_coeff[self.__variables["power"]] = 1
        self.__equalities.append(pulp.LpAffineExpression(power_coeff) == 0)

        unweighted_resources = {
            self.__variables["item:water"]: 0,
            self.__variables["item:iron-ore"]: 1,
            self.__variables["item:copper-ore"]: 1,
            self.__variables["item:limestone"]: 1,
            self.__variables["item:coal"]: 1,
            self.__variables["item:crude-oil"]: 1,
            self.__variables["item:bauxite"]: 1,
            self.__variables["item:caterium-ore"]: 1,
            self.__variables["item:raw-quartz"]: 1,
            self.__variables["item:sulfur"]: 1,
            self.__variables["item:nitrogen-gas"]: 1,
            self.__variables[UNWEIGHTED_RESOURCES]: -1,
        }
        self.__equalities.append(pulp.LpAffineExpression(unweighted_resources) == 0)
        # Proportional to amount of resource on map
        weighted_resources = {
            self.__variables["item:water"]: 0,
            self.__variables["item:iron-ore"]: 1,
            self.__variables["item:copper-ore"]: 3.29,
            self.__variables["item:limestone"]: 1.47,
            self.__variables["item:coal"]: 2.95,
            self.__variables["item:crude-oil"]: 4.31,
            self.__variables["item:bauxite"]: 8.48,
            self.__variables["item:caterium-ore"]: 6.36,
            self.__variables["item:uranium"]: 46.67,
            self.__variables["item:raw-quartz"]: 6.36,
            self.__variables["item:sulfur"]: 13.33,
            self.__variables["item:nitrogen-gas"]: 4.5,  # TODO
            self.__variables[WEIGHTED_RESOURCES]: -1,
        }
        self.__equalities.append(pulp.LpAffineExpression(weighted_resources) == 0)
        # Square root of weighted amounts above
        mean_weighted_resources = {
            self.__variables["item:water"]: 0,
            self.__variables["item:iron-ore"]: 1,
            self.__variables["item:copper-ore"]: 1.81,
            self.__variables["item:limestone"]: 1.21,
            self.__variables["item:coal"]: 1.72,
            self.__variables["item:crude-oil"]: 2.08,
            self.__variables["item:bauxite"]: 2.91,
            self.__variables["item:caterium-ore"]: 2.52,
            self.__variables["item:uranium"]: 6.83,
            self.__variables["item:raw-quartz"]: 2.52,
            self.__variables["item:sulfur"]: 3.65,
            self.__variables["item:nitrogen-gas"]: 2.2,  # TODO
            self.__variables[MEAN_WEIGHTED_RESOURCES]: -1,
        }
        self.__equalities.append(pulp.LpAffineExpression(mean_weighted_resources) == 0)

        alternate_coeffs = {}
        for recipe in self.__db.recipes().values():
            if recipe.is_alternate():
                alternate_coeffs[self.__variables[recipe.var()]] = 1
        alternate_coeffs[self.__variables[ALTERNATE_RECIPES]] = -1
        self.__equalities.append(pulp.LpAffineExpression(alternate_coeffs) == 0)

    def enable_related_recipes(
            self, query: OptimizationQuery, prob: LpProblem, debug: bool = False
    ) -> None:
        query_vars = query.query_vars()
        if UNWEIGHTED_RESOURCES in query_vars:
            return
        if WEIGHTED_RESOURCES in query_vars:
            return
        if MEAN_WEIGHTED_RESOURCES in query_vars:
            return

        # Find inputs and outputs
        inputs = []
        outputs = []

        for category in query.inputs().values():
            for input_var, input in category.elements.items():
                if input_var not in self.__db.items() and input_var != POWER:
                    continue
                if isinstance(input.value, AmountValue) and input.value.value == 0:
                    continue
                inputs.append(input_var)
        for category in query.outputs().values():
            for output_var, output in category.elements.items():
                if output_var not in self.__db.items() and output_var != POWER:
                    continue
                if isinstance(output.value, AmountValue) and output.value.value == 0:
                    continue
                outputs.append(output_var)

        print("inputs:", inputs, "outputs:", outputs)

        enabled_recipes = []
        enabled_power_recipes = []

        # If there is a path from var to the query_input_var, then add all
        # connected recipes.

        def check(input_var, var, connected_recipes, stack):
            # print("Checking if", var, "is connected to", input_var)
            if var == input_var:
                if debug:
                    print("  Found connection!")
                    print("  " + " -> ".join(reversed(stack)))
                return True
            # if var.startswith("resource:"):
            #     return False
            if len(self.__db.recipes_for_product(var)) == 0:
                return False
            is_var_connected = False
            for recipe in self.__db.recipes_for_product(var):
                if recipe.var() in connected_recipes:
                    continue
                if recipe.is_craftable_in_building() and recipe.crafter().var() == "crafter:packager":
                    # We don't want to use the packager recipes to find connections between inputs and outputs
                    continue
                stack.append(recipe.var())
                connected_recipes.append(recipe.var())
                # print("Checking recipe", recipe.var())
                for ingredient in recipe.ingredients():
                    stack.append(ingredient)
                    if check(input_var, ingredient, connected_recipes, stack):
                        is_var_connected = True
                    stack.pop()
                stack.pop()
            return is_var_connected

        for input_var in inputs:
            if input_var == POWER:
                # Nothing to do for power input
                continue
            for output_var in outputs:
                if output_var == POWER:
                    for power_recipe in self.__db.power_recipes().values():
                        connected_recipes = []
                        fuel_var = power_recipe.fuel_item().var()
                        stack = [fuel_var]
                        if debug:
                            print(
                                "\nChecking connection from", input_var, "to", fuel_var
                            )
                        if check(input_var, fuel_var, connected_recipes, stack):
                            if debug:
                                print("enabling connected recipes:", connected_recipes)
                                print("enabling connected power recipe:", power_recipe.var())
                            enabled_recipes.extend(connected_recipes)
                            enabled_power_recipes.append(power_recipe.var())

                else:
                    connected_recipes = []
                    stack = [output_var]
                    if debug:
                        print("\nChecking connection from", input_var, "to", output_var)
                    if check(input_var, output_var, connected_recipes, stack):
                        enabled_recipes.extend(connected_recipes)

        if debug:
            print("enabled recipes:", enabled_recipes)
            print("enabled power recipes:", enabled_power_recipes)

        # Disable any disconnected recipes.
        for recipe_var in self.__db.recipes():
            if recipe_var not in enabled_recipes:
                prob += self.__variables[recipe_var] == 0
        for power_recipe_var in self.__db.power_recipes():
            if power_recipe_var not in enabled_power_recipes:
                prob += self.__variables[power_recipe_var] == 0

    async def optimize(self, query: OptimizationQuery) -> OptimizationResult:
        print("called optimize() with query:\n\n" + str(query) + "\n")

        # TODO: Always max since inputs are negative?
        if isinstance(query.objective(), Output):
            prob = pulp.LpProblem("max-problem", pulp.LpMaximize)
        else:
            prob = pulp.LpProblem("min-problem", pulp.LpMinimize)

        query_vars = query.query_vars()

        # prob += pulp.LpAffineExpression(
        #     [
        #         (self.__variables[query.objective().var], 1)
        #     ]
        # )

        for category in query.inputs().values():
            for input_var, input in category.elements.items():
                variable = self.__variables[input_var]
                if isinstance(input.value, AmountValue):
                    prob += variable >= -input.value.value
                elif isinstance(input.value, AnyValue):
                    prob += variable <= 0
                elif isinstance(input.value, MaximizeValue):
                    prob += -variable

        for category in query.outputs().values():
            for output_var, output in category.elements.items():
                variable = self.__variables[output_var]
                if isinstance(output.value, AmountValue):
                    prob += variable == output.value.value
                elif isinstance(output.value, AnyValue):
                    prob += variable >= 0
                elif isinstance(output.value, MaximizeValue):
                    prob += variable

        # Display the problem before all recipes are added
        # print("Problem:", prob)

        # Add constraints for all item, crafter, and power equalities
        for exp in self.__equalities:
            prob += exp

        # Add item constraints
        for item in self.__db.items().values():
            if item.var() in query_vars:
                continue
            if item.is_resource():
                if query.is_strict_input_category("item"):
                    prob.addConstraint(self.__variables[item.var()] == 0, item.var())
                else:
                    prob.addConstraint(self.__variables[item.var()] <= 0, item.var())
            else:
                if query.is_strict_output_category("item"):
                    prob.addConstraint(self.__variables[item.var()] == 0, item.var())
                else:
                    prob.addConstraint(self.__variables[item.var()] >= 0, item.var())

        if query.is_strict_input_category("crafter"):
            for crafter_var in self.__db.crafters():
                if crafter_var in query_vars:
                    continue
                prob.addConstraint(self.__variables[crafter_var] == 0, crafter_var)
        if query.is_strict_input_category("generator"):
            for generator_var in self.__db.generators():
                if generator_var in query_vars:
                    continue
                prob.addConstraint(self.__variables[generator_var] == 0, generator_var)
        if query.is_strict_input_category("recipe"):
            for recipe_var in self.__db.recipes():
                if recipe_var in query_vars:
                    continue
                prob.addConstraint(self.__variables[recipe_var] == 0, recipe_var)
        if query.is_strict_input_category("power_recipe"):
            for power_recipe_var in self.__db.power_recipes():
                if power_recipe_var in query_vars:
                    continue
                prob.addConstraint(
                    self.__variables[power_recipe_var] == 0, power_recipe_var
                )

        self.enable_related_recipes(query, prob, debug=False)

        # Disable power recipes unless the query specifies something about power
        if not query.has_power_output():
            for power_recipe_var in self.__db.power_recipes():
                prob.addConstraint(
                    self.__variables[power_recipe_var] == 0, power_recipe_var
                )

        # Disable geothermal generators since they are "free" energy.
        if "generator:geo-thermal-generator" not in query_vars:
            prob += self.__variables["generator:geothermal-generator"] == 0

        # Disable biomasss burners since they cannot be automated.
        # if "generator:biomass-burner" not in query_vars:
        #     prob += self.__variables["generator:biomass-burner"] == 0

        # Disable alternate recipes unless the query specifically allows it
        if ALTERNATE_RECIPES not in query_vars:
            prob += self.__variables[ALTERNATE_RECIPES] == 0
        # Display the problem
        # print(prob)

        # Write out complete problem to file
        filename = "output" + os.path.sep + "problem.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(str(prob))

        # Solve
        status = prob.solve()
        result = OptimizationResult(self.__db, self.__variables, prob, status, query)

        for var_name, var in self.__variables.items():
            if var.value() and abs(var.value()) > EPSILON:
                print(f"Variable {var_name} had a value of {var.value()}")

        return result
