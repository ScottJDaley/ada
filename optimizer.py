import pulp
import viz
import fnmatch
import re
from graphviz import Digraph


class ParseException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg

class Optimizer:
	def __init__(self, db):
		self.__db = db

		self.variable_names = []

		# Create problem variables
		self.__variables = {}
		for recipe in self.__db.recipes():
			self.__variables[recipe] = pulp.LpVariable(recipe, lowBound=0)
		for power_recipe in self.__db.power_recipes():
			self.__variables[power_recipe] = pulp.LpVariable(power_recipe, lowBound=0)
		for item in self.__db.items().values():
			self.__variables[item.var()] = pulp.LpVariable(item.var())
		for crafter in self.__db.crafters():
			self.__variables[crafter] = pulp.LpVariable(crafter, lowBound=0)
		for generator_var, generator in self.__db.generators().items():
			self.__variables[generator_var] = pulp.LpVariable(generator_var, lowBound=0)
		self.__variables["power"] = pulp.LpVariable("power")
		self.__partitioned_variables = self.partition_variables_by_match_order()
		print("VARIABLES")
		for var in self.__variables:
			print(var)
		print("PARTITIONED VARIABLES")
		for var_group in self.__partitioned_variables:
			print()
			print(var_group)

		unweighted_resources = {
			"resource:water": 0,
			"resource:iron-ore": 1,
			"resource:copper-ore": 1,
			"resource:limestone": 1,
			"resource:coal": 1,
			"resource:crude-oil": 1,
			"resource:bauxite": 1,
			"resource:caterium-ore": 1,
			"resource:uranium": 1,
			"resource:raw-quartz": 1,
			"resource:sulfur": 1,
		}
		# Proportional to amount of resource on map
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
		# Square root of weighted amounts above
		mean_weighted_resources = {
			"resource:water": 0,
			"resource:iron-ore": 1,
			"resource:copper-ore": 1.81,
			"resource:limestone": 1.21,
			"resource:coal": 1.72,
			"resource:crude-oil": 2.08,
			"resource:bauxite": 2.91,
			"resource:caterium-ore": 2.52,
			"resource:uranium": 6.83,
			"resource:raw-quartz": 2.52,
			"resource:sulfur": 3.65,
		}
		self.built_in_objectives = {
			"unweighted-resources": unweighted_resources,
			"weighted-resources": weighted_resources,
			"mean-weighted-resources": mean_weighted_resources,
		}

		self.equalities = []

		# For each item, create an equality for all inputs and outputs
		# For items:
		#   products - ingredients = net output
		#   products - ingredients - net output = 0
		# For resources:
		#   products - ingredients = - net input
		#   products - ingredients + net input = 0 
		for item_var, item in self.__db.items().items():
			var_coeff = {}  # variable => coefficient
			recipes_for_item = self.__db.recipes_for_product(item_var)
			recipes_from_item = self.__db.recipes_for_ingredient(item_var)
			for recipe in recipes_for_item:
				var_coeff[self.__variables[recipe.var()]] = recipe.product(item_var).minute_rate()
			for recipe in recipes_from_item:
				var_coeff[self.__variables[recipe.var()]] = -recipe.ingredient(item_var).minute_rate()
			if item_var in self.__db.power_recipes_by_fuel():
				power_recipe = self.__db.power_recipes_by_fuel()[item_var]
				var_coeff[self.__variables[power_recipe.var()]] = -power_recipe.fuel_minute_rate()
			if item.is_resource():
				var_coeff[self.__variables[item.var()]] = 1
			else:
				var_coeff[self.__variables[item.var()]] = -1
			self.equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

		# For each type of crafter, create an equality for all recipes that require it
		for crafter_var in self.__db.crafters():
			var_coeff = {}  # variable => coefficient
			for recipe_var, recipe in self.__db.recipes().items():
				if recipe.crafter().var() == crafter_var:
					var_coeff[self.__variables[recipe_var]] = 1
			var_coeff[self.__variables[crafter_var]] = -1
			self.equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

		# For each type of generator, create an equality for power recipes that require it
		for generator_var in self.__db.generators():
			var_coeff = {}  # variable => coefficient
			for power_recipe_var, power_recipe in self.__db.power_recipes().items():
				if power_recipe.generator().var() == generator_var:
					var_coeff[self.__variables[power_recipe_var]] = 1
			var_coeff[self.__variables[generator_var]] = -1
			self.equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

		# Create a single power equality for all recipes and generators
		power_coeff = {}
		for generator_var, generator in self.__db.generators().items():
			power_coeff[self.__variables[generator_var]] = generator.power_production()
		for recipe_var, recipe in self.__db.recipes().items():
			power_coeff[self.__variables[recipe_var]] = -recipe.crafter().power_consumption()
		power_coeff[self.__variables["power"]] = -1
		self.equalities.append(pulp.LpAffineExpression(power_coeff) == 0)

		# Disable geothermal generators since they are "free" energy.
		# TODO: Remove this once there are global maximums for all resources.
		self.equalities.append(self.__variables["generator:geo-thermal-generator"] == 0)

		print("Finished creating optimizer")

	def partition_variables_by_match_order(self):
		match_groups = [
			'resource:.*',
			'item:.*'
			'.*',
		]
		def matches_for(group):
			return [var for var in self.__variables if re.match(group, var)]
		return [matches_for(group) for group in match_groups]

	def parse_variables(self, var_expr):
		for partition in self.partition_variables_by_match_order():
			substring_matched = [var for var in partition if var_expr in var]
			re_matched = [var for var in partition if re.search(var_expr, var)]
			if len(substring_matched) == 1:
				return substring_matched
			if len(substring_matched) > 1:
				raise ParseException("Input '" + var_expr + "' matches multiple variables: " + str(substring_matched))
			if len(substring_matched) == 0 and len(re_matched) > 0:
				return re_matched
		raise ParseException("Input '" + var_expr + "' does not match any variables")

	def parse_constraints(self, *args):
		# First separate constraints by 'and'
		constraints_raw = []
		start_index = 0
		index = 0
		while index <= len(args):
			if index >= len(args) or args[index] == "and":
				constraints_raw.append(args[start_index:index])
				start_index = index + 1
			index += 1

		# Then parse the constraints
		# 	var => (op, bound)
		constraints = {}
		for constraint in constraints_raw:
			if len(constraint) != 3:
				raise ParseException(
				    "Constraint must be in the form {{item}} {{=|<=|>=}} {{number}}.")
			expanded_vars = self.parse_variables(constraint[0])
			operator = constraint[1]
			try:
				bound = int(constraint[2])
			except ValueError:
				raise ParseException("Constraint bound must be an number.")
			if operator != "=" and operator != ">=" and operator != "<=":
				raise ParseException("Constraint operator must be one of {{=|<=|>=}}")
			for var in expanded_vars:
				constraints[var] = (operator, bound)
		return constraints

	def parse_objective(self, *args):
		# TODO: Support expression objectives
		if len(args) > 1:
			raise ParseException(
			    "Input must be in the form {{item}} where {{item}} {{=|<=|>=}} {{number}} ")
		arg0 = args[0]
		objective = {}
		objective_vars = []
		if arg0 in self.built_in_objectives:
			for var_name, coefficient in self.built_in_objectives[arg0].items():
				objective[self.__variables[var_name]] = coefficient
				objective_vars.append(var_name)
		else:
			objective_items = self.parse_variables(arg0)
			for objective_item in objective_items:
				objective[self.__variables[objective_item]] = 1
				objective_vars.append(objective_item)
		return objective, objective_vars

	def parse_input(self, *args):
		# First separate out the {item} where clause
		if len(args) < 2:
			raise ParseException(
			    "Input must be in the form {{item}} where {{item}} {{=|<=|>=}} {{number}} ")
		where_index = -1
		for i in range(len(args)):
			arg = args[i]
			if arg == "where":
				where_index = i
		if where_index <= 0:
			objective, objective_vars = self.parse_objective("weighted-resources")
		else:
			objective, objective_vars = self.parse_objective(*args[:where_index])
		constraints = self.parse_constraints(*args[where_index+1:])
		query_vars = objective_vars
		for var in constraints:
			query_vars.append(var)
		return objective, constraints, query_vars

	def string_solution(self):		
		out = ["INPUT"]
		for variable_name, variable in self.__variables.items():
			if not pulp.value(variable):
				continue
			value = pulp.value(variable)
			if variable_name not in self.__db.items():
				continue
			item = self.__db.items()[variable_name]
			if item.is_resource() and value < 0:
				continue
			if not item.is_resource() and value > 0:
				continue
			friendly_name = self.__db.items()[variable_name].human_readable_name()
			out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("OUTPUT")
		for variable_name, variable in self.__variables.items():
			if not pulp.value(variable):
				continue
			value = pulp.value(variable)
			if variable_name not in self.__db.items():
				continue
			item = self.__db.items()[variable_name]
			if item.is_resource() and value > 0:
				continue
			if not item.is_resource() and value < 0:
				continue
			friendly_name = self.__db.items()[variable_name].human_readable_name()
			out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("RECIPES")
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "recipe:"):
				continue
			if pulp.value(variable):
				friendly_name = self.__db.recipes()[variable_name].human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("POWER RECIPES")
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "power-recipe:"):
				continue
			if pulp.value(variable):
				friendly_name = self.__db.power_recipes()[variable_name].fuel_item().human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("CRAFTERS")
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "crafter:"):
				continue
			if pulp.value(variable):
				friendly_name = self.__db.crafters()[variable_name].human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("GENERATORS")
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "generator:"):
				continue
			if pulp.value(variable):
				friendly_name = self.__db.generators()[variable_name].human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("NET POWER")
		net_power = 0
		if pulp.value(self.__variables["power"]):
			net_power = pulp.value(self.__variables["power"])
		out.append(str(net_power) + " MW")
		for var in self.__variables:
			if pulp.value(self.__variables[var]) and pulp.value(self.__variables[var]) != 0:
				print("Variable", var, pulp.value(self.__variables[var]))
		return '\n'.join(out)

	def graph_viz_solution(self):
		s = Digraph('structs', format='png', filename='output.gv',
				node_attr={'shape': 'record'})

		# item => {source => amount}
		sources = {}
		# item => {sink => amount}
		sinks = {}
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "recipe:"):
				continue
			if not pulp.value(variable) or pulp.value(variable) == 0:
				continue
			recipe = self.__db.recipes()[variable_name]
			friendly_name = recipe.human_readable_name()
			s.node(recipe.viz_name(), viz.get_recipe_viz_label(recipe, pulp.value(variable)), shape="plaintext")
			for item, ingredient in recipe.ingredients().items():
				if item not in sinks:
					sinks[item] = {}
				ingredient_amount = pulp.value(variable) * ingredient.minute_rate()
				sinks[item][recipe.viz_name()] = ingredient_amount
			for item, product in recipe.products().items():
				if item not in sources:
					sources[item] = {}
				product_amount = pulp.value(variable) * product.minute_rate()
				sources[item][recipe.viz_name()] = product_amount

		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "power-recipe:"):
				continue
			if not pulp.value(variable) or pulp.value(variable) == 0:
				continue
			power_recipe = self.__db.power_recipes()[variable_name]
			friendly_name = power_recipe.human_readable_name()
			s.node(power_recipe.viz_name(), viz.get_power_recipe_label(power_recipe, pulp.value(variable)), shape="plaintext")
			fuel_item = power_recipe.fuel_item()
			if fuel_item.var() not in sinks:
				sinks[fuel_item.var()] = {}
			sinks[fuel_item.var()][power_recipe.viz_name()] = pulp.value(variable) * power_recipe.fuel_minute_rate()

		for variable_name, variable in self.__variables.items():
			if not pulp.value(variable):
				continue
			value = pulp.value(variable)
			if variable_name not in self.__db.items():
				continue
			item = self.__db.items()[variable_name]
			if item.is_resource() and value < 0:
				continue
			if not item.is_resource() and value > 0:
				continue
			friendly_name = self.__db.items()[variable_name].human_readable_name()
			s.node(item.viz_name(), viz.get_input_viz_label(friendly_name, pulp.value(variable)), shape="plaintext")
			if item not in sources:
				sources[item.var()] = {}
			sources[item.var()][item.viz_name()] = pulp.value(variable)

		for variable_name, variable in self.__variables.items():
			if not pulp.value(variable):
				continue
			value = pulp.value(variable)
			if variable_name not in self.__db.items():
				continue
			item = self.__db.items()[variable_name]
			if item.is_resource() and value > 0:
				continue
			if not item.is_resource() and value < 0:
				continue
			friendly_name = self.__db.items()[variable_name].human_readable_name()
			s.node(item.viz_name(), viz.get_output_viz_label(friendly_name, pulp.value(variable)), shape="plaintext")
			if item not in sinks:
				sinks[item.var()] = {}
			sinks[item.var()][item.viz_name()] = pulp.value(variable)
		
		net_power = 0
		if pulp.value(self.__variables["power"]):
			net_power = pulp.value(self.__variables["power"])
		s.node("power", str(net_power) + " MW Net Power")

		# Connect each source to all sinks of that item
		for item_var, item_sources in sources.items():
			item = self.__db.items()[item_var]
			for source, _ in item_sources.items():
				if item_var not in sinks:
					print("Could not find", item_var, "in sinks")
					continue
				for sink, sink_amount in sinks[item_var].items():
					s.edge(source, sink, label=viz.get_edge_label(item.human_readable_name(), sink_amount))

		# s.view() # Opens the image or pdf using default program
		s.render() # Only creates output file

	def optimize(self, max, *args):
		# Parse input
		# {item} where {item} {=|<=|>=} {number} and ...
		try:
			objective, constraints, query_vars = self.parse_input(*args)
		except ParseException as err:
			return err

		for query_var in query_vars:
			print("query var:", query_var)
		for item, expr in constraints.items():
			print("constraint:", item, expr[0], expr[1])

		# Ojective: to maximize the production of on an item given the constraints.
		if max:
			prob = pulp.LpProblem('max-problem', pulp.LpMaximize)
		else:
			prob = pulp.LpProblem('min-problem', pulp.LpMinimize)

		if objective:
			# TODO: Support more flexible objective
			print("OBJECTIVE:", objective)
			prob += pulp.LpAffineExpression(objective)
		else:
			return "Must have objective"

		# Add constraints for all item, crafter, and power equalities
		for exp in self.equalities:
			prob += exp

		# Add item constraints
		for item_var, item in self.__db.items().items():
			if item_var in query_vars:
				continue
			if item.is_resource():
				# Allow resource input
				prob += self.__variables[item.var()] >= 0
			else:
				# Don't require any other inputs and eliminate byproducts
				prob += self.__variables[item_var] == 0

		# Don't use power recipes unless the query specifies something about power
		if "power" not in query_vars:
			for power_recipe_var in self.__db.power_recipes():
				prob += self.__variables[power_recipe_var] == 0

		# Add flexible constraint for resources
		# for resource_var, multiplier in self.weighted_resources.items():
		# 	resource = resource_var.name
		# 	if resource in constraints or resource == max_item:
		# 		continue
		# 	constraint = pulp.LpConstraint(e=resource_var, name=resource, sense=pulp.LpConstraintLE, rhs=0)
		# 	penalty = multiplier
		# 	elastic_prob = constraint.makeElasticSubProblem(penalty=penalty, proportionFreeBound=0)
		# 	prob.extend(elastic_prob)

		# Add provided contraints
		for item, expr in constraints.items():
			op = expr[0]
			bound = expr[1]
			if op == "=":
				prob += self.__variables[item] == bound
			elif op == ">=":
				prob += self.__variables[item] >= bound
			else: # op == "<="
				prob += self.__variables[item] <= bound
		
		# Display the problem 
		# print(prob) 

		# Solve
		status = prob.solve()
		solution = ""
		solution += self.string_solution() + "\n\n"
		if status is pulp.LpStatusOptimal:
			solution += self.string_solution() + "\n\n"
			self.graph_viz_solution()
			print("Done generating GraphViz")
		solution += "Solver status: " + pulp.LpStatus[status]

		solution += "\n\nOBJECTIVE VALUE\n"
		solution += str(pulp.value(prob.objective))
			
		# print(solution)

		return solution

		
			

		

		

			
