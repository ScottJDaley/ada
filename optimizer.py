import json
import pulp


class ParseException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg


class Optimizer:
	# TODO: Let users specify alternate recipes and building unlocks
	def __init__(self, skip_alternates=False):
		# Parse data file
		with open("data.json") as f:
			data = json.load(f)

		self.variable_names = []

		# Create a dictionary of items, item class name => item slug name
		self.item_class_names = {}
		self.items = []
		for item in data["items"].values():
			item_name = item["slug"]
			self.item_class_names[item["className"]] = item_name
			self.variable_names.append("input:" + item_name)
			self.variable_names.append("output:" + item_name)
			self.items.append(item_name)

		# Create a list of resources
		self.resources = []
		for resource in data["resources"].values():
			self.resources.append(self.item_class_names[resource["item"]])

		# Create a dictionary from product => [recipe => product amount]
		self.recipes_for_product = {}
		# Create a dictionary from ingredient => [recipe => ingredient amount]
		self.recipes_for_ingredient = {}

		for recipe in data["recipes"].values():
			if not recipe["inMachine"]:
				continue
			if skip_alternates and recipe["alternate"]:
				print("Skipping ", recipe["name"])
				continue
			recipe_name = "Recipe: " + recipe["name"]
			self.variable_names.append(recipe_name)
			for ingredient in recipe["ingredients"]:
				ingredient_name = self.item_class_names[ingredient["item"]]
				if ingredient_name not in self.recipes_for_ingredient:
					self.recipes_for_ingredient[ingredient_name] = {}
				self.recipes_for_ingredient[ingredient_name][recipe_name] = 60 * \
				    ingredient["amount"] / recipe["time"]
			for product in recipe["products"]:
				product_name = self.item_class_names[product["item"]]
				if product_name not in self.recipes_for_product:
					self.recipes_for_product[product_name] = {}
				self.recipes_for_product[product_name][recipe_name] = 60 * \
				    product["amount"] / recipe["time"]

		# Create problem variables
		self.variables = {}
		for variable_name in self.variable_names:
			self.variables[variable_name] = pulp.LpVariable(variable_name, lowBound=0)

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

		self.recipe_expressions = []

		for item in self.items:
			recipe_amounts = {}  # variable => coefficient
			if item in self.recipes_for_product:
				for recipe, amount in self.recipes_for_product[item].items():
					recipe_amounts[self.variables[recipe]] = amount
			if item in self.recipes_for_ingredient:
				for recipe, amount in self.recipes_for_ingredient[item].items():
					recipe_amounts[self.variables[recipe]] = -amount
			recipe_amounts[self.variables["input:" + item]] = 1
			recipe_amounts[self.variables["output:" + item]] = -1
			self.recipe_expressions.append(pulp.LpAffineExpression(recipe_amounts) == 0)

		print("Finished creating optimizer")

	def parse_item(self, item):
		normalized_item = item
		if not str.startswith(item, "input:") and not str.startswith(item, "output:"):
			if item in self.resources:
				normalized_item = "input:" + item
			else:
				normalized_item = "output:" + item
		if normalized_item not in self.variables:
			raise ParseException("Unknown item variable: " + item)
		return normalized_item

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
		# 	item => (op, bound)
		constraints = {}
		for constraint in constraints_raw:
			if len(constraint) != 3:
				raise ParseException(
				    "Constraint must be in the form {{item}} {{=|<=|>=}} {{number}}.")
			item = self.parse_item(constraint[0])
			operator = constraint[1]
			try:
				bound = int(constraint[2])
			except ValueError:
				raise ParseException("Constraint bound must be an number.")
			if operator != "=" and operator != ">=" and operator != "<=":
				raise ParseException("Constraint operator must be one of {{=|<=|>=}}")
			constraints[item] = (operator, bound)
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
				objective[self.variables[var_name]] = coefficient
				objective_vars.append(var_name)
		else:
			objective_item = self.parse_item(arg0)
			objective[self.variables[objective_item]] = 1
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

	def get_solution(self):		
		out = ["INPUT"]
		for variable_name, variable in self.variables.items():
			if not str.startswith(variable_name, "input:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				out.append(variable_name[6:] + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("OUTPUT")
		for variable_name, variable in self.variables.items():
			if not str.startswith(variable_name, "output:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				out.append(variable_name[7:] + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("RECIPES")
		for variable_name, variable in self.variables.items():
			if not str.startswith(variable_name, "Recipe:"):
				continue
			if pulp.value(variable):
				out.append(variable_name + ": " + str(pulp.value(variable)))
		return '\n'.join(out)

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
			prob = pulp.LpProblem('Maximize Problem', pulp.LpMaximize)
		else:
			prob = pulp.LpProblem('Minimize Problem', pulp.LpMinimize)

		if objective:
			# TODO: Support more flexible objective
			print("OBJECTIVE:", objective)
			prob += pulp.LpAffineExpression(objective)
		else:
			return "Must have objective"

		# Add recipe constraints
		for exp in self.recipe_expressions:
			prob += exp

		# Add item constraints
		for item in self.items:
			# Don't require any other inputs
			item_input = "input:" + item
			if item_input not in query_vars:
				prob += self.variables[item_input] == 0
			# Eliminate byproducts
			item_output = "output:" + item
			if item_output not in query_vars:
				prob += self.variables[item_output] == 0

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
				prob += self.variables[item] == bound
			elif op == ">=":
				prob += self.variables[item] >= bound
			else: # op == "<="
				prob += self.variables[item] <= bound
		
		# Display the problem 
		# print(prob) 

		# Solve
		status = prob.solve()
		solution = self.get_solution() + "\n\nSolver status: " + pulp.LpStatus[status]
			
		# print(solution)

		# print()
		# print("OBJECTIVE VALUE")
		# print(pulp.value(prob.objective))
		return solution
		
	def max(self, *args):
		print("calling max with", len(args), "arguments:", ', '.join(args))
		return self.optimize(True, *args)

	def min(self, *args):
		print("calling min with", len(args), "arguments:", ', '.join(args))
		return self.optimize(False, *args)
		
			

		

		

			
