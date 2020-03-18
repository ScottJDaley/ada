import pulp
from graphviz import Digraph

class Solution:
    def __init__(self, db, vars, prob, status):
        self.__db = db
        self.__prob = prob
        self.__vars = vars
        self.__status = status
    def __has_value(self, var):
        return self.__vars[var].value() and self.__vars[var].value() != 0

    def __get_value(self, var):
        return self.__vars[var].value()

    def __get_section(self, title, objs):
        found_any = False
        out = []
        out.append(title)
        for obj in objs:
            var = obj.var()
            if self.__has_value(var):
                found_any = True
                out.append(obj.human_readable_name() + ": " + str(self.__get_value(var)))
        out.append("")
        if found_any:
            return out
        return []

    def __string_solution(self):
        out = []
        out.extend(self.__get_section("INPUT", [item.input() for item in self.__db.items().values()]))
        out.extend(self.__get_section("OUTPUT", [item.output() for item in self.__db.items().values()]))
        out.extend(self.__get_section("RECIPES", self.__db.recipes().values()))
        out.extend(self.__get_section("CRAFTERS", self.__db.crafters().values()))
        out.extend(self.__get_section("GENERATORS", self.__db.generators().values()))
        out.append("NET POWER")
        net_power = 0
        if self.__has_value("power"):
            net_power =  self.__get_value("power")
        out.append(str(net_power) + " MW")
        out.append("")
        out.append("OBJECTIVE VALUE")
        out.append(str(self.__prob.objective.value()))
        return '\n'.join(out)

    def __str__(self):
        if self.__status is pulp.LpStatusNotSolved:
            return "No solution has been found."
        if self.__status is pulp.LpStatusUndefined:
            return "Not solution has been found."
        if self.__status is pulp.LpStatusInfeasible:
            return "Solution is infeasible, try removing a constraint or allowing a byproduct (e.g. rubber >= 0)"
        if self.__status is pulp.LpStatusUnbounded:
            return "Solution is unbounded, try adding a constraint"
        else:
            return self.__string_solution()

    def __add_nodes(self, s, objs):
        for obj in objs:
            var = obj.var()
            if not self.__has_value(var):
                continue
            amount = self.__get_value(var)
            s.node(obj.viz_name(), obj.viz_label(amount), shape="plaintext")

    def generate_graph_viz(self, filename):
        s = Digraph('structs', format='png', filename=filename,
                node_attr={'shape': 'record'})
        
        sources = {} # item => {source => amount}
        sinks = {} # item => {sink => amount}

        def add_to_target(item_var, targets, target, amount):
            if item_var not in targets:
                targets[item_var]= {}
            targets[item_var][target] = amount

        # items
        self.__add_nodes(s, [item.input() for item in self.__db.items().values()])
        self.__add_nodes(s, [item.output() for item in self.__db.items().values()])
        for item in self.__db.items().values():
            input_var = item.input().var()
            if self.__has_value(input_var):
                add_to_target(item.var(), sources, item.input().viz_name(), self.__get_value(input_var))
            output_var = item.output().var()
            if self.__has_value(output_var):
                add_to_target(item.var(), sinks, item.output().viz_name(), self.__get_value(output_var))
        # recipes
        self.__add_nodes(s, self.__db.recipes().values())
        for recipe in self.__db.recipes().values():
            if not self.__has_value(recipe.var()):
                continue
            recipe_amount = self.__get_value(recipe.var())
            for item_var, ingredient in recipe.ingredients().items():
                ingredient_amount = recipe_amount * ingredient.minute_rate()
                add_to_target(item_var, sinks, recipe.viz_name(), ingredient_amount)
            for item_var, product in recipe.products().items():
                product_amount = recipe_amount * product.minute_rate()
                add_to_target(item_var, sources, recipe.viz_name(), product_amount)
        # power recipes
        self.__add_nodes(s, self.__db.power_recipes().values())
        for power_recipe in self.__db.power_recipes().values():
            if not self.__has_value(power_recipe.var()):
                continue
            fuel_item = power_recipe.fuel_item()
            fuel_amount = self.__get_value(power_recipe.var()) * power_recipe.fuel_minute_rate()
            add_to_target(fuel_item.var(), sinks, power_recipe.viz_name(), fuel_amount)
        # power
        net_power = 0
        if self.__has_value("power"):
            net_power = self.__get_value("power")
        s.node("power", str(net_power) + " MW Net Power")

        def get_edge_label(item, amount):
            return str(round(amount, 2)) + '/m\n' +  item

        # Connect each source to all sinks of that item
        for item_var, item_sources in sources.items():
            item = self.__db.items()[item_var]
            for source, _ in item_sources.items():
                if item_var not in sinks:
                    print("Could not find", item_var, "in sinks")
                    continue
                for sink, sink_amount in sinks[item_var].items():
                    s.edge(source, sink, label=get_edge_label(item.human_readable_name(), sink_amount))

        s.render()



