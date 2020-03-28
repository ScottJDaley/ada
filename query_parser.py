import pyparsing as pp
from pyparsing import pyparsing_common as ppc
import inflect
from functools import partial

p = inflect.engine()


class QueryParser:

    def __init__(self, db):

        # Keywords
        output_kw = pp.Keyword("produce") | pp.Keyword(
            "make") | pp.Keyword("create") | pp.Keyword("output")
        input_kw = pp.Keyword("from") | pp.Keyword(
            "input") | pp.Keyword("using")
        include_kw = pp.Keyword("with") | pp.Keyword("including")
        exclude_kw = pp.Keyword("without") | pp.Keyword("excluding")
        objective_kw = pp.Keyword("?").setParseAction(
            partial(self.push_value, "?"))
        any_kw = (pp.Keyword("any") | pp.Keyword("_")
                  ).setParseAction(partial(self.push_value, "_"))
        only_kw = pp.Keyword("only").setParseAction(self.set_is_only)
        no_kw = (pp.Keyword("no") | pp.Keyword("0") |
                 "-").setParseAction(partial(self.push_value, 0))
        and_kw = pp.Keyword("and") | "+"
        nor_kw = pp.Keyword("and") | pp.Keyword("or") | pp.Keyword("nor")
        power_kw = pp.Keyword("power").setParseAction(
            partial(self.push_var, "power"))
        tickets_kw = pp.Keyword("tickets").setParseAction(
            partial(self.push_var, "tickets"))
        space_kw = pp.Keyword("space").setParseAction(
            partial(self.push_var, "space"))
        unweighted_resources_kw = (pp.Keyword("unweighted resources") | pp.Keyword(
            "resources")).setParseAction(partial(self.push_var, "unweighted-resources"))
        weighted_resources_kw = pp.Keyword("weighted resources").setParseAction(
            partial(self.push_var, "weighted-resources"))
        alternate_recipes_kw = pp.Keyword("alternate recipes").setParseAction(
            partial(self.push_var, "alternate-recipes"))
        byproducts_kw = pp.Keyword("byproducts").setParseAction(
            partial(self.push_var, "byproducts"))

        # end_of_expr = output_kw | input_kw | include_kw | exclude_kw | and_kw

        # Expressions for variable names
        # Consider going back to looking for any string up until end_of_expr.
        # Then as a parse action, check if it matches. That way we can give a
        # better failure message.
        item_expr = self.get_var_expr(
            [item for item in db.items().values() if not item.is_resource()])
        resource_expr = self.get_var_expr(
            [item for item in db.items().values() if item.is_resource()])
        recipe_expr = self.get_var_expr(db.recipes().values())
        crafter_expr = self.get_var_expr(db.crafters().values())
        generator_expr = self.get_var_expr(db.generators().values())

        output_var = power_kw | tickets_kw | item_expr
        input_var = power_kw | space_kw | unweighted_resources_kw | \
            weighted_resources_kw | resource_expr | item_expr
        # TODO: Consider moving building expressions to inputs instead so that a
        # value can be used. Or do both.
        include_var = alternate_recipes_kw | byproducts_kw | recipe_expr | \
            crafter_expr | generator_expr
        exclude_var = alternate_recipes_kw | byproducts_kw | recipe_expr | \
            crafter_expr | generator_expr

        include_value_expr = (only_kw | no_kw).setParseAction(self.handle_value)

        number_value = ppc.integer.setParseAction(self.push_number_value)
        value = number_value | any_kw | objective_kw
        value_expr = ((pp.Optional(only_kw) + pp.Optional(value))
                      | no_kw).setParseAction(self.handle_value)

        output_expr = (pp.Optional(value_expr) +
                       output_var).setParseAction(self.output_action)
        input_expr = (pp.Optional(value_expr) +
                      input_var).setParseAction(self.input_action)
        include_expr = (pp.Optional(include_value_expr) +
                        include_var).setParseAction(self.include_action)
        exclude_expr = exclude_var.setParseAction(self.exclude_action)

        outputs = output_expr + pp.ZeroOrMore(and_kw + output_expr)
        inputs = input_expr + pp.ZeroOrMore(and_kw + input_expr)
        includes = include_expr + pp.ZeroOrMore(and_kw + include_expr)
        excludes = exclude_expr + pp.ZeroOrMore(nor_kw + exclude_expr)

        outputs_expr = output_kw + outputs
        inputs_expr = input_kw + inputs
        includes_expr = include_kw + includes
        excludes_expr = exclude_kw + excludes

        self.__query_syntax = outputs_expr + pp.Optional(inputs_expr) + \
            pp.Optional(includes_expr) + pp.Optional(excludes_expr)

        self.reset()

    def reset_intermidiates(self):
        self.__last_vars = []
        self.__last_value = None
        self.__is_only = False

    def push_number_value(self, toks):
        self.__last_value = toks[0]

    def push_value(self, value, toks):
        self.__last_value = value

    def set_is_only(self, toks):
        self.__is_only = True

    def handle_value(self, toks):
        if not self.__last_value:
            self.__last_value = "_"

    def push_var(self, var, toks):
        self.__last_vars.append(var)
        print(var)

    def get_var_expr(self, vars):
        var_names = []
        for var in vars:
            singular = pp.CaselessLiteral(var.human_readable_name().lower())
            plural = pp.CaselessLiteral(
                p.plural(var.human_readable_name().lower()))
            var_names.append((plural | singular).setParseAction(
                partial(self.push_var, var.var())))
        return pp.Or(var_names)

    def output_action(self, toks):
        print("output:", toks)
        if self.__last_value == "?":
            self.__objective.is_max = True
            self.__objective.vars = self.__last_vars
        elif self.__last_value == "_":
            for var in self.__last_vars:
                self.__ge_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__eq_constraints[var] = int(self.__last_value)
        self.reset_intermidiates()

    def input_action(self, toks):
        print("input:", toks)
        if self.__last_value == "?":
            self.__objective.is_max = False
            self.__objective.vars = self.__last_vars
        elif self.__last_value == "_":
            for var in self.__last_vars:
                self.__le_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__eq_constraints[var] = -int(self.__last_value)
        self.reset_intermidiates()

    def include_action(self, toks):
        print("include:", toks)
        if self.__last_value == "_":
            for var in self.__last_vars:
                self.__ge_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__eq_constraints[var] = self.__last_value
        self.reset_intermidiates()

    def exclude_action(self, toks):
        print("exclude:", toks)
        if self.__last_value == "_":
            for var in self.__last_vars:
                self.__le_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__eq_constraints[var] = self.__last_value
        for var in self.__last_vars:
            self.__eq_constraints[var] = 0
        self.reset_intermidiates()

    def grammar(self):
        return self.__query_syntax

    def reset(self):
        self.reset_intermidiates()

        class Objective:
            pass
        self.__objective = Objective()
        self.__objective.is_max = True
        # vars will be added in objective, vars[0] + vars[1] + ...
        self.__objective.vars = []
        self.__eq_constraints = {}  # var = value
        self.__ge_constraints = {}  # var >= value
        self.__le_constraints = {}  # var <= value

    def print_output(self):
        print("Objective:")
        func = "minimize"
        if self.__objective.is_max:
            func = "maximize"
        print("  " + func + " " + " + ".join(self.__objective.vars))
        print("Constraints:")
        for var, val in self.__eq_constraints.items():
            print("  " + var + " = " + str(val))
        for var, val in self.__ge_constraints.items():
            print("  " + var + " >= " + str(val))
        for var, val in self.__le_constraints.items():
            print("  " + var + " <= " + str(val))

    def test(self, test_str):
        self.reset()
        try:
            results = self.__query_syntax.parseString(test_str, parseAll=True)
        except pp.ParseException as pe:
            print("\"" + test_str + "\" ==> failed parse:")
            print((pe.loc+1)*" " + "^")
            print(str(pe), "\n")
        else:
            print("\"" + test_str + "\" ==> parsing succeeded:\n",
                  results, "\n")
            self.print_output()
            print()
