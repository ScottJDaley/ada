

class Query:
    def __init__(self):
        self.maximize_objective = True
        self.objective_coefficients = {}
        self.eq_constraints = {}
        self.ge_constraints = {}
        self.le_constraints = {}

    def __str__(self):
        out = []
        out.append("Objective:")
        func = "minimize"
        if self.maximize_objective:
            func = "maximize"

        objective = [str(coeff) + "*" + var for var,
                     coeff in self.objective_coefficients.items()]
        out.append("  " + func + " " + " + ".join(objective))
        out.append("Constraints")
        for var, val in self.eq_constraints.items():
            out.append("  " + var + " = " + str(val))
        for var, val in self.ge_constraints.items():
            out.append("  " + var + " >= " + str(val))
        for var, val in self.le_constraints.items():
            out.append("  " + var + " <= " + str(val))
        return "\n".join(out)

    def print(self):
        print(self)
