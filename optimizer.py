import pulp
from result import Result
from query_parser import QueryParser, ParseException

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
            self.__variables[item.input().var()] = pulp.LpVariable(item.input().var(), lowBound=0)
            self.__variables[item.output().var()] = pulp.LpVariable(item.output().var(), lowBound=0)
        for crafter in self.__db.crafters():
            self.__variables[crafter] = pulp.LpVariable(crafter, lowBound=0)
        for generator_var, generator in self.__db.generators().items():
            self.__variables[generator_var] = pulp.LpVariable(generator_var, lowBound=0)
        self.__variables["power"] = pulp.LpVariable("power")
        
        self.__byproducts = [
            "item:fuel:output",
            "item:polymer-resin:output",
            "item:plastic:output",
            "item:heavy-oil-residue:output",
            "item:rubber:output",
            "item:silica:output",
        ]

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
            var_coeff[self.__variables[item.input().var()]] = 1
            var_coeff[self.__variables[item.output().var()]] = -1
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

        print("Finished creating optimizer")

    async def optimize(self, request_input_fn, max, *args):
        # Parse input
        # {item} where {item} {=|<=|>=} {number} and ...
        try:
            parser = QueryParser(self.__variables)
            objective, constraints, query_vars = await parser.parse_input(request_input_fn, *args)
        except ParseException as err:
            return err.msg, None

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
            print()
            prob += pulp.LpAffineExpression(objective)
        else:
            return "Must have objective", None

        normalized_input = ["NORMALIZED INPUT:"]
        objective_exp = pulp.LpAffineExpression(objective)
        if max:
            normalized_input.append("max " + str(objective_exp) + " where:")
        else:
            normalized_input.append("min " + str(objective_exp))
        for item, expr in constraints.items():
            normalized_input.append("  " + item + " " + expr[0] + " " + str(expr[1]))
        print('\n'.join(normalized_input))


        # Add constraints for all item, crafter, and power equalities
        for exp in self.equalities:
            prob += exp

        # Add item constraints
        for item in self.__db.items().values():
            # Don't require any other inputs
            if item.input().var() not in query_vars:
                if item.is_resource():
                    prob += self.__variables[item.input().var()] >= 0
                else:
                    prob += self.__variables[item.input().var()] == 0
            # Eliminate unneccessary byproducts
            if item.output().var() not in query_vars:
                # if item in self.__byproducts:
                #     prob += self.__variables[item.input().var()] >= 0
                # else:
                #     prob += self.__variables[item.output().var()] == 0
                prob += self.__variables[item.output().var()] == 0

        # Disable power recipes unless the query specifies something about power
        if "power" not in query_vars:
            for power_recipe_var in self.__db.power_recipes():
                prob += self.__variables[power_recipe_var] == 0

        # Disable geothermal generators since they are "free" energy.
        if "generator:geo-thermal-generator" not in query_vars:
            prob += self.__variables["generator:geo-thermal-generator"] == 0

        # Disable biomasss burners since they cannot be automated.
        if "generator:biomass-burner" not in query_vars:
            prob += self.__variables["generator:biomass-burner"] == 0

        # Add flexible constraint for resources
        # for resource_var, multiplier in self.weighted_resources.items():
        #     resource = resource_var.name
        #     if resource in constraints or resource == max_item:
        #         continue
        #     constraint = pulp.LpConstraint(e=resource_var, name=resource, sense=pulp.LpConstraintLE, rhs=0)
        #     penalty = multiplier
        #     elastic_prob = constraint.makeElasticSubProblem(penalty=penalty, proportionFreeBound=0)
        #     prob.extend(elastic_prob)

        # Add flexible constraint for byproducts
        # for byproduct in self.__byproducts:
        #     if byproduct in query_vars:
        #         continue
        #     constraint = pulp.LpConstraint(e=self.__variables[byproduct], name=byproduct, sense=pulp.LpConstraintLE, rhs=0)
        #     penalty = -1000
        #     elastic_prob = constraint.makeElasticSubProblem(penalty=penalty, proportionFreeBound=0)
        #     prob.extend(elastic_prob)

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
        result = Result(self.__db, self.__variables, prob, status)

        # TODO: This doesn't work because a constraint of x >= 0 doesn't
        # override a previous constraint of x == 0.
        #
        # if not found_non_zero_var:
        #     print("Problem was too constrained, allowing byproducts")
        #     for byproduct in self.__byproducts:
        #         prob += self.__variables[byproduct] >= 0
        #     status = prob.solve()

        return result

        
            

        

        

            
