import pulp
from result import Result

POWER = "power"
UNWEIGHTED_RESOURCES = "unweighted-resources"
WEIGHTED_RESOURCES = "weighted-resources"
MEAN_WEIGHTED_RESOURCES = "mean-weighted-resources"
ALTERNATE_RECIPES = "alternate-recipes"


class Optimizer:
    def __init__(self, db):
        self.__db = db

        self.variable_names = []

        # Create problem variables
        self.__variables = {}
        for recipe in self.__db.recipes():
            self.__variables[recipe] = pulp.LpVariable(recipe, lowBound=0)
        for power_recipe in self.__db.power_recipes():
            self.__variables[power_recipe] = pulp.LpVariable(
                power_recipe, lowBound=0)
        for item in self.__db.items().values():
            self.__variables[item.var()] = pulp.LpVariable(item.var())
        for crafter in self.__db.crafters():
            self.__variables[crafter] = pulp.LpVariable(crafter, lowBound=0)
        for generator_var, generator in self.__db.generators().items():
            self.__variables[generator_var] = pulp.LpVariable(
                generator_var, lowBound=0)
        self.__variables[POWER] = pulp.LpVariable(POWER)
        self.__variables[UNWEIGHTED_RESOURCES] = pulp.LpVariable(
            UNWEIGHTED_RESOURCES)
        self.__variables[WEIGHTED_RESOURCES] = pulp.LpVariable(
            WEIGHTED_RESOURCES)
        self.__variables[MEAN_WEIGHTED_RESOURCES] = pulp.LpVariable(
            MEAN_WEIGHTED_RESOURCES)
        self.__variables[ALTERNATE_RECIPES] = pulp.LpVariable(
            ALTERNATE_RECIPES, lowBound=0)

        self.__byproducts = [
            "item:fuel:output",
            "item:polymer-resin:output",
            "item:plastic:output",
            "item:heavy-oil-residue:output",
            "item:rubber:output",
            "item:silica:output",
        ]

        self.__equalities = []

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
                var_coeff[self.__variables[recipe.var()]] = recipe.product(
                    item_var).minute_rate()
            for recipe in recipes_from_item:
                var_coeff[self.__variables[recipe.var()]] = - \
                    recipe.ingredient(item_var).minute_rate()
            if item_var in self.__db.power_recipes_by_fuel():
                power_recipe = self.__db.power_recipes_by_fuel()[item_var]
                var_coeff[self.__variables[power_recipe.var()]] = - \
                    power_recipe.fuel_minute_rate()
            var_coeff[self.__variables[item.var()]] = -1
            # var_coeff[self.__variables[item.output().var()]] = -1
            self.__equalities.append(pulp.LpAffineExpression(var_coeff) == 0)

        # For each type of crafter, create an equality for all recipes that require it
        for crafter_var in self.__db.crafters():
            var_coeff = {}  # variable => coefficient
            for recipe_var, recipe in self.__db.recipes().items():
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
            power_coeff[self.__variables[generator_var]
                        ] = generator.power_production()
        for recipe_var, recipe in self.__db.recipes().items():
            power_coeff[self.__variables[recipe_var]] = - \
                recipe.crafter().power_consumption()
        power_coeff[self.__variables["power"]] = -1
        self.__equalities.append(pulp.LpAffineExpression(power_coeff) == 0)

        unweighted_resources = {
            self.__variables["resource:water"]: 0,
            self.__variables["resource:iron-ore"]: 1,
            self.__variables["resource:copper-ore"]: 1,
            self.__variables["resource:limestone"]: 1,
            self.__variables["resource:coal"]: 1,
            self.__variables["resource:crude-oil"]: 1,
            self.__variables["resource:bauxite"]: 1,
            self.__variables["resource:caterium-ore"]: 1,
            self.__variables["resource:uranium"]: 1,
            self.__variables["resource:raw-quartz"]: 1,
            self.__variables["resource:sulfur"]: 1,
            self.__variables[UNWEIGHTED_RESOURCES]: -1,
        }
        self.__equalities.append(
            pulp.LpAffineExpression(unweighted_resources) == 0)
        # Proportional to amount of resource on map
        weighted_resources = {
            self.__variables["resource:water"]: 0,
            self.__variables["resource:iron-ore"]: 1,
            self.__variables["resource:copper-ore"]: 3.29,
            self.__variables["resource:limestone"]: 1.47,
            self.__variables["resource:coal"]: 2.95,
            self.__variables["resource:crude-oil"]: 4.31,
            self.__variables["resource:bauxite"]: 8.48,
            self.__variables["resource:caterium-ore"]: 6.36,
            self.__variables["resource:uranium"]: 46.67,
            self.__variables["resource:raw-quartz"]: 6.36,
            self.__variables["resource:sulfur"]: 13.33,
            self.__variables[WEIGHTED_RESOURCES]: -1,
        }
        self.__equalities.append(
            pulp.LpAffineExpression(weighted_resources) == 0)
        # Square root of weighted amounts above
        mean_weighted_resources = {
            self.__variables["resource:water"]: 0,
            self.__variables["resource:iron-ore"]: 1,
            self.__variables["resource:copper-ore"]: 1.81,
            self.__variables["resource:limestone"]: 1.21,
            self.__variables["resource:coal"]: 1.72,
            self.__variables["resource:crude-oil"]: 2.08,
            self.__variables["resource:bauxite"]: 2.91,
            self.__variables["resource:caterium-ore"]: 2.52,
            self.__variables["resource:uranium"]: 6.83,
            self.__variables["resource:raw-quartz"]: 2.52,
            self.__variables["resource:sulfur"]: 3.65,
            self.__variables[MEAN_WEIGHTED_RESOURCES]: -1,
        }
        self.__equalities.append(
            pulp.LpAffineExpression(mean_weighted_resources) == 0)

        alternate_coeffs = {}
        for recipe in self.__db.recipes().values():
            if recipe.is_alternate():
                alternate_coeffs[self.__variables[recipe.var()]] = 1
        alternate_coeffs[self.__variables[ALTERNATE_RECIPES]] = -1
        self.__equalities.append(pulp.LpAffineExpression(alternate_coeffs) == 0)

        print("Finished creating optimizer")

    def enable_related_recipes(self, query, prob):
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

        for var, coeff in query.objective_coefficients.items():
            if var not in self.__db.items() and var != POWER:
                continue
            if coeff < 0:
                inputs.append(var)
            elif coeff >= 0:
                outputs.append(var)
        for var, value in query.eq_constraints.items():
            if var not in self.__db.items() and var != POWER:
                continue
            if value < 0:
                inputs.append(var)
            elif value > 0:
                outputs.append(var)
        for var, value in query.le_constraints.items():
            if var not in self.__db.items() and var != POWER:
                continue
            if value <= 0:
                inputs.append(var)
            elif value > 0:
                outputs.append(var)
        for var, value in query.ge_constraints.items():
            if var not in self.__db.items() and var != POWER:
                continue
            if value < 0:
                inputs.append(var)
            elif value >= 0:
                outputs.append(var)

        enabled_recipes = []
        enabled_power_recipes = []

        # If there is a path from var to the query_input_var, then add all
        # connected recipes.

        def check(input_var, var, connected_recipes, stack):
            # print("Checking if", var, "is connected to", input_var)
            if var == input_var:
                print("  Found connection!")
                print("  " + " -> ".join(reversed(stack)))
                return True
            if var.startswith("resource:"):
                return False
            if len(self.__db.recipes_for_product(var)) == 0:
                return False
            is_var_connected = False
            for recipe in self.__db.recipes_for_product(var):
                if recipe.var() in connected_recipes:
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
                        print("\nChecking connection from",
                              input_var, "to", fuel_var)
                        if check(input_var, fuel_var, connected_recipes, stack):
                            enabled_recipes.extend(connected_recipes)
                            enabled_power_recipes.append(power_recipe.var())

                else:
                    connected_recipes = []
                    stack = [output_var]
                    print("\nChecking connection from",
                          input_var, "to", output_var)
                    if check(input_var, output_var, connected_recipes, stack):
                        enabled_recipes.extend(connected_recipes)

        print(enabled_recipes)
        print(enabled_power_recipes)

        # Disable any disconnected recipes.
        for recipe_var in self.__db.recipes():
            if recipe_var not in enabled_recipes:
                prob += self.__variables[recipe_var] == 0
        for power_recipe_var in self.__db.power_recipes():
            if power_recipe_var not in enabled_power_recipes:
                prob += self.__variables[power_recipe_var] == 0

    async def optimize(self, query):
        print("called optimize() with query:\n\n" + str(query) + "\n")

        # TODO: Always max since inputs are negative?
        if query.maximize_objective:
            prob = pulp.LpProblem('max-problem', pulp.LpMaximize)
        else:
            prob = pulp.LpProblem('min-problem', pulp.LpMinimize)

        query_vars = query.query_vars()

        prob += pulp.LpAffineExpression([(self.__variables[var], coeff)
                                         for var, coeff in query.objective_coefficients.items()])

        print("eq:", query.eq_constraints)
        print("ge:", query.ge_constraints)
        print("le:", query.le_constraints)

        for var, bound in query.eq_constraints.items():
            prob += self.__variables[var] == bound
        for var, bound in query.ge_constraints.items():
            prob += self.__variables[var] >= bound
        for var, bound in query.le_constraints.items():
            prob += self.__variables[var] <= bound

        # Display the problem before all recipes are added
        print(prob)
        print(query_vars)

        # Add constraints for all item, crafter, and power equalities
        for exp in self.__equalities:
            prob += exp

         # Add item constraints
        for item in self.__db.items().values():
            if item.var() in query_vars:
                continue
            if item.is_resource():
                if query.strict_inputs:
                    prob.addConstraint(
                        self.__variables[item.var()] == 0, item.var())
                else:
                    prob.addConstraint(
                        self.__variables[item.var()] <= 0, item.var())
            else:
                if query.strict_outputs:
                    prob.addConstraint(
                        self.__variables[item.var()] == 0, item.var())
                else:
                    prob.addConstraint(
                        self.__variables[item.var()] >= 0, item.var())

        if query.strict_crafters:
            for crafter_var in self.__db.crafters():
                if crafter_var in query_vars:
                    continue
                prob.addConstraint(
                    self.__variables[crafter_var] == 0, crafter_var)
        if query.strict_generators:
            for generator_var in self.__db.generators():
                if generator_var in query_vars:
                    continue
                prob.addConstraint(
                    self.__variables[generator_var] == 0, generator_var)
        if query.strict_recipes:
            for recipe_var in self.__db.recipes():
                if recipe_var in query_vars:
                    continue
                prob.addConstraint(
                    self.__variables[recipe_var] == 0, recipe_var)
        if query.strict_power_recipes:
            for power_recipe_var in self.__db.power_recipes():
                if power_recipe_var in query_vars:
                    continue
                prob.addConstraint(
                    self.__variables[power_recipe_var] == 0, power_recipe_var)

        self.enable_related_recipes(query, prob)

        # Disable power recipes unless the query specifies something about power
        # if "power" not in query_vars:
        #     for power_recipe_var in self.__db.power_recipes():
        #         prob += self.__variables[power_recipe_var] == 0

        # Disable geothermal generators since they are "free" energy.
        if "generator:geo-thermal-generator" not in query_vars:
            prob += self.__variables["generator:geo-thermal-generator"] == 0

        # Disable biomasss burners since they cannot be automated.
        if "generator:biomass-burner" not in query_vars:
            prob += self.__variables["generator:biomass-burner"] == 0

        # Display the problem
        # print(prob)

        # Write out complete problem to file
        with open('problem.txt', 'w') as f:
            f.write(str(prob))

        # Solve
        status = prob.solve()
        result = Result(self.__db, self.__variables, prob, status)

        return result
