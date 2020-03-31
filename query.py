

class Query:
    def __init__(self):
        self.maximize_objective = True
        self.objective_coefficients = {}
        self.eq_constraints = {}
        self.ge_constraints = {}
        self.le_constraints = {}
        self.strict_inputs = False
        self.strict_outputs = False
        self.strict_crafters = False
        self.strict_generators = False
        self.strict_recipes = False
        self.strict_power_recipes = False

    def __str__(self):
        out = []
        out.append("Objective:")
        func = "minimize"
        if self.maximize_objective:
            func = "maximize"

        objective = [str(coeff) + "*" + var for var,
                     coeff in self.objective_coefficients.items()]
        out.append("  " + func + " " + " + ".join(objective))
        out.append("Constraints:")
        for var, val in self.eq_constraints.items():
            out.append("  " + var + " = " + str(val))
        for var, val in self.ge_constraints.items():
            out.append("  " + var + " >= " + str(val))
        for var, val in self.le_constraints.items():
            out.append("  " + var + " <= " + str(val))
        if self.strict_inputs:
            out.append("  strict inputs")
        if self.strict_outputs:
            out.append("  strict outputs")
        if self.strict_crafters:
            out.append("  strict crafters")
        if self.strict_generators:
            out.append("  strict generators")
        if self.strict_recipes:
            out.append("  strict recipes")
        if self.strict_power_recipes:
            out.append("  strict power recipes")
        return "\n".join(out)

    def print(self):
        print(self)

    def query_vars(self):
        query_vars = []
        query_vars.extend(self.objective_coefficients.keys())
        for var in self.eq_constraints:
            query_vars.append(var)
        for var in self.ge_constraints:
            query_vars.append(var)
        for var in self.le_constraints:
            query_vars.append(var)
        return query_vars
