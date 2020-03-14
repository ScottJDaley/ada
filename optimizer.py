import pulp
import viz
import fnmatch
from graphviz import Digraph


class ParseException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg


class Optimizer:
	# TODO: Let users specify alternate recipes and building unlocks
	def __init__(self, db):
		self.__db = db

		self.variable_names = []

		# Create problem variables
		self.__variables = {}
		for recipe in self.__db.recipes():
			self.__variables[recipe] = pulp.LpVariable(recipe, lowBound=0)
		for item in self.__db.items():
			item_input = "input:" + item
			item_output = "output:" + item
			self.__variables[item_input] = pulp.LpVariable(item_input, lowBound=0)
			self.__variables[item_output] = pulp.LpVariable(item_output, lowBound=0)
		for building in self.__db.buildings():
			print(building)
			self.__variables[building] = pulp.LpVariable(building, lowBound=0)
		self.__variables["input:power"] = pulp.LpVariable("input:power", lowBound=0)
		self.__variables["output:power"] = pulp.LpVariable("output:power", lowBound=0)

		unweighted_resources = {
			"input:water": 0,
			"input:iron-ore": 1,
			"input:copper-ore": 1,
			"input:limestone": 1,
			"input:coal": 1,
			"input:crude-oil": 1,
			"input:bauxite": 1,
			"input:caterium-ore": 1,
			"input:uranium": 1,
			"input:raw-quartz": 1,
			"input:sulfur": 1,
		}
		# Proportional to amount of resource on map
		weighted_resources = {
			"input:water": 0,
			"input:iron-ore": 1,
			"input:copper-ore": 3.29,
			"input:limestone": 1.47,
			"input:coal": 2.95,
			"input:crude-oil": 4.31,
			"input:bauxite": 8.48,
			"input:caterium-ore": 6.36,
			"input:uranium": 46.67,
			"input:raw-quartz": 6.36,
			"input:sulfur": 13.33,
		}
		# Square root of weighted amounts above
		mean_weighted_resources = {
			"input:water": 0,
			"input:iron-ore": 1,
			"input:copper-ore": 1.81,
			"input:limestone": 1.21,
			"input:coal": 1.72,
			"input:crude-oil": 2.08,
			"input:bauxite": 2.91,
			"input:caterium-ore": 2.52,
			"input:uranium": 6.83,
			"input:raw-quartz": 2.52,
			"input:sulfur": 3.65,
		}
		self.built_in_objectives = {
			"unweighted-resources": unweighted_resources,
			"weighted-resources": weighted_resources,
			"mean-weighted-resources": mean_weighted_resources,
		}

		self.equalities = []

		# For each item, create an equality for all inputs and outputs
		for item in self.__db.items():
			var_coeff = {}  # variable => coefficient
			recipes_for_item = self.__db.recipes_for_product(item)
			recipes_from_item = self.__db.recipes_for_ingredient(item)
			for recipe in recipes_for_item:
				var_coeff[self.__variables[recipe.var()]] = recipe.product(item).minute_rate()
			for recipe in recipes_from_item:
				var_coeff[self.__variables[recipe.var()]] = -recipe.ingredient(item).minute_rate()
			var_coeff[self.__variables["input:" + item]] = 1
			var_coeff[self.__variables["output:" + item]] = -1
			self.equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

		# For each building, create an equality for all recipes that use it
		for building in self.__db.buildings():
			var_coeff = {}  # variable => coefficient
			for recipe_var, recipe in self.__db.recipes().items():
				if recipe.building().var() == building:
					var_coeff[self.__variables[recipe_var]] = 1
			var_coeff[self.__variables[building]] = -1
			print(pulp.LpAffineExpression(var_coeff))
			self.equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

		# Create a single power equality for all recipes
		power_coeff = {}
		for recipe_var, recipe in self.__db.recipes().items():
			power_coeff[self.__variables[recipe_var]] = recipe.building().power()
		power_coeff[self.__variables["input:power"]] = -1
		power_coeff[self.__variables["output:power"]] = 1
		self.equalities.append(pulp.LpAffineExpression(power_coeff) == 0)

		print("Finished creating optimizer")

	def parse_variable(self, var):
		if var in self.__variables:
			return var
		normalized_var = var
		if not str.startswith(var, "input:") and not str.startswith(var, "output:"):
			if var in self.__db.resources():
				normalized_var = "input:" + var
			else:
				normalized_var = "output:" + var
		if normalized_var not in self.__variables:
			return None
		return normalized_var

	def parse_variables(self, var_expr):
		var = self.parse_variable(var_expr)
		matched_vars = set()
		if var:
			matched_vars.add(self.parse_variable(var_expr))
		matched_vars.update(fnmatch.filter(self.__variables, var_expr))
		for var in matched_vars:
			print("Matched var:", var)
		if len(matched_vars) == 0:
			raise ParseException("Unknown variable: " + var_expr)
		return matched_vars

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
			objective_item = self.parse_variable(arg0)
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
			if str.endswith(variable_name, "power") or not str.startswith(variable_name, "input:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				friendly_name = self.__db.items()[variable_name[6:]].human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("OUTPUT")
		for variable_name, variable in self.__variables.items():
			if str.endswith(variable_name, "power") or not str.startswith(variable_name, "output:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				friendly_name = self.__db.items()[variable_name[7:]].human_readable_name()
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
		out.append("BUILDINGS")
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "building:"):
				continue
			if pulp.value(variable):
				friendly_name = self.__db.buildings()[variable_name].human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("POWER")
		input_power = 0
		if pulp.value(self.__variables["input:power"]):
			input_power = pulp.value(self.__variables["input:power"])
		output_power = 0
		if pulp.value(self.__variables["output:power"]):
			output_power = pulp.value(self.__variables["output:power"])
		out.append("Input: " + str(input_power) + " MW")
		out.append("Output: " + str(output_power) + " MW")
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
			if pulp.value(variable):
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
			if str.endswith(variable_name, "power") or not str.startswith(variable_name, "input:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				item = self.__db.items()[variable_name[6:]]
				friendly_name = item.human_readable_name()
				s.node(item.var(), viz.get_input_viz_label(friendly_name, pulp.value(variable)), shape="plaintext")
				if item not in sources:
					sources[item.var()] = {}
				sources[item.var()][item.var()] = pulp.value(variable)

		for variable_name, variable in self.__variables.items():
			if str.endswith(variable_name, "power") or not str.startswith(variable_name, "output:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				item = self.__db.items()[variable_name[7:]]
				friendly_name = item.human_readable_name()
				s.node(item.var(), viz.get_output_viz_label(friendly_name, pulp.value(variable)), shape="plaintext")
				if item not in sinks:
					sinks[item.var()] = {}
				sinks[item.var()][item.var()] = pulp.value(variable)

		# Connect each source to all sinks of that item
		for item, item_sources in sources.items():
			for source, _ in item_sources.items():
				if item not in sinks:
					print("Could not find", item, "in sinks")
					continue
				for sink, sink_amount in sinks[item].items():
					s.edge(source, sink, label=viz.get_edge_label(item, sink_amount))

		# s.view() # Opens the image or pdf using default program
		s.render() # Only creates output file

	def optimize(self, max, *args):
		# Parse input
		# {item} where {item} {=|<=|>=} {number} and ...
		try:
			objective, constraints, query_vars = self.parse_input(*args)
		except ParseException as err:
			return err

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

		# Add constraints for all item, building, and power equalities
		for exp in self.equalities:
			prob += exp

		# Add item constraints
		for item in self.__db.items():
			# Don't require any other inputs
			item_input = "input:" + item
			if item_input not in query_vars:
				prob += self.__variables[item_input] == 0
			# Eliminate byproducts
			item_output = "output:" + item
			if item_output not in query_vars:
				prob += self.__variables[item_output] == 0

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
		if status is pulp.LpStatusOptimal:
			solution += self.string_solution() + "\n\n"
			self.graph_viz_solution()
			print("Done generating GraphViz")
		solution += "Solver status: " + pulp.LpStatus[status]
			
		# print(solution)

		# print()
		# print("OBJECTIVE VALUE")
		# print(pulp.value(prob.objective))
		return solution

		
			

		

		

			
