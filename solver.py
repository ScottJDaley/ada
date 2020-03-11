import pulp
import json

skip_alternates = False

# Parse data file
with open("data.json") as f:
    data = json.load(f)

variable_names = []

# Create a dictionary of items, item class name => item name
item_class_names = {}
for item in data["items"].values():
    item_name = item["name"]
    item_class_names[item["className"]] = item["name"]
    variable_names.append(item_name)

# Create a list of resources
resources = []
for resource in data["resources"].values():
    resources.append(item_class_names[resource["item"]])

# Create a dictionary from product => [recipe => product amount]
recipes_for_product = {}
# Create a dictionary from ingredient => [recipe => ingredient amount]
recipes_for_ingredient = {}

for recipe in data["recipes"].values():
    if not recipe["inMachine"]:
        continue
    if skip_alternates and recipe["alternate"]:
        print("Skipping ", recipe["name"])
        continue
    recipe_name = "Recipe: " + recipe["name"]
    variable_names.append(recipe_name)
    for ingredient in recipe["ingredients"]:
        ingredient_name = item_class_names[ingredient["item"]]
        if ingredient_name not in recipes_for_ingredient:
            recipes_for_ingredient[ingredient_name] = {}
        recipes_for_ingredient[ingredient_name][recipe_name] = ingredient["amount"]
    for product in recipe["products"]:
        product_name = item_class_names[product["item"]]
        if product_name not in recipes_for_product:
            recipes_for_product[product_name] = {}
        recipes_for_product[product_name][recipe_name] = product["amount"]

# Create problem variables
variables = {}
for variable_name in variable_names:
    if variable_name in resources:
        variables[variable_name] = pulp.LpVariable(variable_name, upBound = 0)
    else:
        variables[variable_name] = pulp.LpVariable(variable_name, lowBound = 0)
        # if variable_name == "Iron Rod":
        #   variables[variable_name] = pulp.LpVariable(variable_name)
        # else:
        #   variables[variable_name] = pulp.LpVariable(variable_name, lowBound = 0)

unweighted = {
    variables["Water"]: 0,
    variables["Iron Ore"]: 1,
    variables["Copper Ore"]: 1,
    variables["Limestone"]: 1,
    variables["Coal"]: 1,
    variables["Crude Oil"]: 1,
    variables["Bauxite"]: 1,
    variables["Caterium Ore"]: 1,
    variables["Uranium"]: 1,
    variables["Raw Quartz"]: 1,
    variables["Sulfur"]: 1,
}
# Proportional to amount of resource on map
weighted = {
    variables["Water"]: 0,
    variables["Iron Ore"]: 1,
    variables["Copper Ore"]: 3.29,
    variables["Limestone"]: 1.47,
    variables["Coal"]: 2.95,
    variables["Crude Oil"]: 4.31,
    variables["Bauxite"]: 8.48,
    variables["Caterium Ore"]: 6.36,
    variables["Uranium"]: 46.67,
    variables["Raw Quartz"]: 6.36,
    variables["Sulfur"]: 13.33,
}
# Square root of weighted amounts above
mean_weighted = {
    variables["Water"]: 0,
    variables["Iron Ore"]: 1,
    variables["Copper Ore"]: 1.81,
    variables["Limestone"]: 1.21,
    variables["Coal"]: 1.72,
    variables["Crude Oil"]: 2.08,
    variables["Bauxite"]: 2.91,
    variables["Caterium Ore"]: 2.52,
    variables["Uranium"]: 6.83,
    variables["Raw Quartz"]: 2.52,
    variables["Sulfur"]: 3.65,
}

# Create a LP Maximization problem 
prob = pulp.LpProblem('Problem', pulp.LpMaximize)

# Objective Function

# Minimize raw resource usage.
# prob += pulp.LpAffineExpression(unweighted)
# prob += pulp.LpAffineExpression(mean_weighted)
# prob += pulp.LpAffineExpression(weighted) + 1000*variables["Heavy Modular Frame"]
prob += variables["Fuel"]

# Input
# prob += variables["Iron Ore"] >= -60
# prob += variables["Iron Rod"] >= -400

# Output

# We want exactly 35 iron ingots per minute
# prob += variables["Iron Ingot"] == 35
# prob += variables["Water"] == 0
prob += variables["Crude Oil"] == -240

# Eliminate byproducts
# prob += variables["Rubber"] == 0
# prob += variables["Fabric"] == 0
prob += variables["Packaged Water"] == 0
# prob += variables["Polymer Resin"] == 0
# prob += variables["Empty Canister"] == 0
# prob += variables["Plastic"] == 0
# prob += variables["Rotor"] == 0
# prob += variables["Screw"] == 0

# Maximize production give raw resources
# prob += variables["Modular Frame"]
# prob += variables["Iron Ore"] == -60

prob += variables["Copper Ore"] == 0

# Constraints: 

# We want a constraint for each item that represents the following:
#   total item production equals
#        i) the quantity of a particular recipe that produces that
#           item times the number of the item that the recipes
#           produces.
#       ii) minus the quantity of a particular recipe that requires
#           that item times the number of the item that the recipes
#           requires.
#      iii) for all recipes that use or produce that item.
# Net resources between inputs and ingredients should be 0.
# 1. Iterate through all items
# 2. Iterate through the recipes that produce that item
# 3. Multiple the recipe variable by the product amount
# 4. Iterate through the recipes that consume that item
# 5. Multiple the recipe variable by the negative ingredient amount
# 6. Add a negative term for the item itself, to cancel out with
#    any product that is being specified in the goal constraints
#    above.

for item in data["items"].values():
    item_name = item["name"]
    recipe_amounts = {} # variable => coefficient
    if item_name in recipes_for_product:
        for recipe, amount in recipes_for_product[item_name].items():
            recipe_amounts[variables[recipe]] = amount
    if item_name in recipes_for_ingredient:
        for recipe, amount in recipes_for_ingredient[item_name].items():
            recipe_amounts[variables[recipe]] = -amount 
    recipe_amounts[variables[item_name]] = -1
    prob += pulp.LpAffineExpression(recipe_amounts) == 0
    if item_name not in resources and item_name != "Fuel" and item_name != "Polymer Resin":
    	prob += variables[item_name] == 0
    if item_name == "Iron Rod":
        print(pulp.LpAffineExpression(recipe_amounts) == 0)
    # Add flexible constraints for byproducts? Ideally they would be zero.
  
# Display the problem 
# print(prob) 
  
status = prob.solve()   # Solver 
print("Solver status:", pulp.LpStatus[status])   # The solution status 
print()
  
# Printing the final solution 
print("INPUT")
for variable in variables.values():
    if pulp.value(variable) and pulp.value(variable) < 0:
        print(variable.name + ":", -pulp.value(variable))
print()
print("OUTPUT")
for variable_name, variable in variables.items():
    if str.startswith(variable.name, "Recipe:"):
        continue
    if pulp.value(variable) and pulp.value(variable) > 0:
        print(variable.name + ":", pulp.value(variable))
print()
print("RECIPES")
for variable in variables.values():
    if not str.startswith(variable.name, "Recipe:"):
        continue
    if pulp.value(variable):
        print(variable.name + ":", pulp.value(variable))
print()
print("OBJECTIVE VALUE")
print(pulp.value(prob.objective))
        

