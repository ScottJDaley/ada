import pulp


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

		for item in self.__db.items():
			recipe_amounts = {}  # variable => coefficient
			recipes_for_item = self.__db.recipes_for_product(item)
			recipes_from_item = self.__db.recipes_for_ingredient(item)
			for recipe in recipes_for_item:
				recipe_amounts[self.__variables[recipe.var()]] = recipe.product_amount(item)
			for recipe in recipes_from_item:
				recipe_amounts[self.__variables[recipe.var()]] = -recipe.ingredient_amount(item)
			recipe_amounts[self.__variables["input:" + item]] = 1
			recipe_amounts[self.__variables["output:" + item]] = -1
			self.recipe_expressions.append(pulp.LpAffineExpression(recipe_amounts) == 0)

		print("Finished creating optimizer")

	def parse_variable(self, var):
		normalized_var = var
		if not str.startswith(var, "input:") and not str.startswith(var, "output:") and not str.startswith(var, "recipe:"):
			if var in self.__db.resources():
				normalized_var = "input:" + var
			else:
				normalized_var = "output:" + var
		if normalized_var not in self.__variables:
			raise ParseException("Unknown variable: " + var)
		return normalized_var

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
			var = self.parse_variable(constraint[0])
			operator = constraint[1]
			try:
				bound = int(constraint[2])
			except ValueError:
				raise ParseException("Constraint bound must be an number.")
			if operator != "=" and operator != ">=" and operator != "<=":
				raise ParseException("Constraint operator must be one of {{=|<=|>=}}")
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

	def get_solution(self):		
		out = ["INPUT"]
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "input:"):
				continue
			if pulp.value(variable) and pulp.value(variable) > 0:
				friendly_name = self.__db.items()[variable_name[6:]].human_readable_name()
				out.append(friendly_name + ": " + str(pulp.value(variable)))
		out.append("")
		out.append("OUTPUT")
		for variable_name, variable in self.__variables.items():
			if not str.startswith(variable_name, "output:"):
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
			prob = pulp.LpProblem('max-problem', pulp.LpMaximize)
		else:
			prob = pulp.LpProblem('min-problem', pulp.LpMinimize)

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
		solution = self.get_solution() + "\n\nSolver status: " + pulp.LpStatus[status]
			
		# print(solution)

		# print()
		# print("OBJECTIVE VALUE")
		# print(pulp.value(prob.objective))
		return solution

		
			

		

		

			
