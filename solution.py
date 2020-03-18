import pulp

class Solution:
    def __init__(self, db, vars, prob, status):
        self.__db = db
        self.__prob = prob
        self.__vars = vars
        self.__status = status
    def __has_value(self, var):
        return self.__vars[var].value() and self.__vars[var].value() != 0

    def __get_value(self, var):
        return self.__vars[var].value()

    def __get_section(self, title, objs, get_var=lambda obj : obj.var()):
        found_any = False
        out = []
        out.append(title)
        for obj in objs:
            var = get_var(obj)
            if self.__has_value(var):
                found_any = True
                out.append(obj.human_readable_name() + ": " + str(self.__get_value(var)))
        out.append("")
        if found_any:
            return out
        return []

    def __string_solution(self):
        out = []
        out.extend(self.__get_section("INPUT", self.__db.items().values(), get_var=lambda item: item.input_var()))
        out.extend(self.__get_section("OUTPUT", self.__db.items().values(), get_var=lambda item: item.output_var()))
        out.extend(self.__get_section("RECIPES", self.__db.recipes().values()))
        out.extend(self.__get_section("CRAFTERS", self.__db.crafters().values()))
        out.extend(self.__get_section("GENERATORS", self.__db.generators().values()))
        out.append("NET POWER")
        net_power = 0
        if self.__has_value("power"):
            net_power =  self.__get_value("power")
        out.append(str(net_power) + " MW")
        out.append("")
        out.append("OBJECTIVE VALUE")
        out.append(str(self.__prob.objective.value()))
        return '\n'.join(out)

    def __str__(self):
        if self.__status is pulp.LpStatusNotSolved:
            return "No solution has been found."
        if self.__status is pulp.LpStatusUndefined:
            return "Not solution has been found."
        if self.__status is pulp.LpStatusInfeasible:
            return "Solution is infeasible, try removing a constraint or allowing a byproduct (e.g. rubber >= 0)"
        if self.__status is pulp.LpStatusUnbounded:
            return "Solution is unbounded, try adding a constraint"
        else:
            return self.__string_solution()

        