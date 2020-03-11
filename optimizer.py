import json
import pulp


class ParseException(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg


class Optimizer:
	#TODO: Let users specify alternate recipes and building unlocks
	def __init__(self, skip_alternates = False):
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
			self.variable_names.append(item_name)
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
				self.recipes_for_ingredient[ingredient_name][recipe_name] = 60 * ingredient["amount"]  / recipe["time"]
			for product in recipe["products"]:
				product_name = self.item_class_names[product["item"]]
				if product_name not in self.recipes_for_product:
					self.recipes_for_product[product_name] = {}
				self.recipes_for_product[product_name][recipe_name] = 60 * product["amount"] / recipe["time"]

		# Create problem variables
		self.variables = {}
		for variable_name in self.variable_names:
			if variable_name in self.resources:
				self.variables[variable_name] = pulp.LpVariable(variable_name, upBound = 0)
			else:
				self.variables[variable_name] = pulp.LpVariable(variable_name, lowBound = 0)

		self.unweighted_resources = {
			self.variables["water"]: 0,
			self.variables["iron-ore"]: 1,
			self.variables["copper-ore"]: 1,
			self.variables["limestone"]: 1,
			self.variables["coal"]: 1,
			self.variables["crude-oil"]: 1,
			self.variables["bauxite"]: 1,
			self.variables["caterium-ore"]: 1,
			self.variables["uranium"]: 1,
			self.variables["raw-quartz"]: 1,
			self.variables["sulfur"]: 1,
		}
		# Proportional to amount of resource on map
		self.weighted_resources = {
			self.variables["water"]: 0,
			self.variables["iron-ore"]: 1,
			self.variables["copper-ore"]: 3.29,
			self.variables["limestone"]: 1.47,
			self.variables["coal"]: 2.95,
			self.variables["crude-oil"]: 4.31,
			self.variables["bauxite"]: 8.48,
			self.variables["caterium-ore"]: 6.36,
			self.variables["uranium"]: 46.67,
			self.variables["raw-quartz"]: 6.36,
			self.variables["sulfur"]: 13.33,
		}
		# Square root of weighted amounts above
		self.mean_weighted_resources = {
			self.variables["water"]: 0,
			self.variables["iron-ore"]: 1,
			self.variables["copper-ore"]: 1.81,
			self.variables["limestone"]: 1.21,
			self.variables["coal"]: 1.72,
			self.variables["crude-oil"]: 2.08,
			self.variables["bauxite"]: 2.91,
			self.variables["caterium-ore"]: 2.52,
			self.variables["uranium"]: 6.83,
			self.variables["raw-quartz"]: 2.52,
			self.variables["sulfur"]: 3.65,
		}

		self.recipe_expressions = []

		for item in self.items:
			recipe_amounts = {} # variable => coefficient
			if item in self.recipes_for_product:
				for recipe, amount in self.recipes_for_product[item].items():
					recipe_amounts[self.variables[recipe]] = amount
			if item in self.recipes_for_ingredient:
				for recipe, amount in self.recipes_for_ingredient[item].items():
					recipe_amounts[self.variables[recipe]] = -amount 
			recipe_amounts[self.variables[item]] = -1
			self.recipe_expressions.append(pulp.LpAffineExpression(recipe_amounts) == 0)

		print("Finished creating optimizer")

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
				raise ParseException("Constraint must be in the form {{item}} {{=|<=|>=}} {{number}}.")
			item = constraint[0]
			if item not in self.items:
				raise ParseException("Constraint is for unknown item: " + item)
			operator = constraint[1]
			try: 
				bound = int(constraint[2])
			except ValueError:
				raise ParseException("Constraint bound must be an number.")
			if operator != "=" and operator != ">=" and operator != "<=":
				raise ParseException("Constraint operator must be one of {{=|<=|>=}}")
			constraints[item] = (operator, bound)
		return constraints

	def parse_max_expression(self, *args):
		# First separate out the {item} where clause
		if len(args) < 2:
			raise ParseException("Input must be in the form {{item}} where {{item}} {{=|<=|>=}} {{number}} ")
		item = args[0]
		if item not in self.items:
			raise ParseException("Unknown item:" + item)
		if args[1] != "where":
			raise ParseException("Input must be in the form {{item}} where {{item}} {{=|<=|>=}} {{number}} ")
		return item, self.parse_constraints(*args[2:])

	def print_solution(self):
		print("INPUT")
		for variable_name, variable in self.variables.items():
			if str.startswith(variable_name, "Recipe:"):
				continue
			if pulp.value(variable) and pulp.value(variable) < 0:
				print(variable_name + ":", -pulp.value(variable))
		print()
		print("OUTPUT")
		for variable_name, variable in self.variables.items():
			if str.startswith(variable_name, "Recipe:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				print(variable_name + ":", pulp.value(variable))
		print()
		print("RECIPES")
		for variable_name, variable in self.variables.items():
			if not str.startswith(variable_name, "Recipe:"):
				continue
			if pulp.value(variable):
				print(variable_name + ":", pulp.value(variable))
		
	
	def max(self, *args):
		print("calling max with", len(args), "arguments:", ', '.join(args))

		# Parse input
		# {item} where {item} {=|<=|>=} {number} and ...
		try:
			max_item, constraints = self.parse_max_expression(*args)
		except ParseException as err:
			print(err)
			return

		for item, expr in constraints.items():
			print("constraint:", item, expr[0], expr[1])

		# Ojective: to maximize the production on an item given the constraints.
		prob = pulp.LpProblem('Problem', pulp.LpMaximize)

		prob += self.variables[max_item]

		# Add recipe constraints
		for exp in self.recipe_expressions:
			prob += exp

		# Add item constraints
		for item in self.items:
			# Eliminate byproducts
			if item != max_item and item not in constraints and item not in self.resources:
				prob += self.variables[item] == 0

		# Add resource constraints for any unspecified
		for resource in self.resources:
			if resource != max_item and resource not in constraints:
				prob += self.variables[resource] == 0

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
		print("Solver status:", pulp.LpStatus[status])
		print()
		
		# Printing the final solution 
		self.print_solution()

		print()
		print("OBJECTIVE VALUE")
		print(pulp.value(prob.objective))

	def min(self, *args):
		print("calling min with", len(args), "arguments:", ', '.join(args))

		# Parse input
		# {item} {=|<=|>=} {number} and ...
		try:
			constraints = self.parse_constraints(*args)
		except ParseException as err:
			print(err)
			return
		
		for item, expr in constraints.items():
			print("constraint:", item, expr[0], expr[1])
		
		# Objective: to minimize raw resource usage to achieve the constraints.
		# This is represented as a maximize problem since resource variables are negative 
		prob = pulp.LpProblem('Problem', pulp.LpMaximize)
		# TODO: Let users change this?
		prob += pulp.LpAffineExpression(self.mean_weighted_resources)

		# Add recipe constraints
		for exp in self.recipe_expressions:
			prob += exp

		# Add item constraints
		for item in self.items:
			# Eliminate byproducts
			if item not in constraints and item not in self.resources:
				prob += self.variables[item] == 0

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
		print("Solver status:", pulp.LpStatus[status])
		print()
		
		# Printing the final solution 
		self.print_solution()

		print()
		print("OBJECTIVE VALUE")
		print(pulp.value(prob.objective))
		
			

		

		

			
