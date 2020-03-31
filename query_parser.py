import pyparsing as pp
from pyparsing import pyparsing_common as ppc
import inflect
from functools import partial
from query import Query

p = inflect.engine()


class QueryParseException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


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
        power_recipe_expr = self.get_var_expr(db.power_recipes().values())
        crafter_expr = self.get_var_expr(db.crafters().values())
        generator_expr = self.get_var_expr(db.generators().values())

        output_var = power_kw | tickets_kw | item_expr
        input_var = power_kw | space_kw | unweighted_resources_kw | \
            weighted_resources_kw | resource_expr | item_expr
        # TODO: Consider moving building expressions to inputs instead so that a
        # value can be used. Or do both.
        include_var = alternate_recipes_kw | byproducts_kw | recipe_expr | \
            power_recipe_expr | crafter_expr | generator_expr
        exclude_var = alternate_recipes_kw | byproducts_kw | recipe_expr | \
            power_recipe_expr | crafter_expr | generator_expr

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

        self.__last_vars = []
        self.__last_value = None
        self.__is_only = False
        self.__query = None

    def reset_intermidiates(self):
        self.__last_vars = []
        self.__last_value = None
        self.__is_only = False

    def push_number_value(self, toks):
        self.__last_value = toks[0]

    def push_value(self, value, _):
        self.__last_value = value

    def set_is_only(self, _):
        self.__is_only = True

    def handle_value(self, _):
        if not self.__last_value:
            self.__last_value = "_"

    def push_var(self, var, _):
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

    def output_action(self, _):
        if self.__last_value == "?":
            # Maximize the outputs
            self.__query.maximize_objective = True
            for var in self.__last_vars:
                self.__query.objective_coefficients[var] = 1
        elif self.__last_value == "_":
            for var in self.__last_vars:
                self.__query.ge_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__query.eq_constraints[var] = int(self.__last_value)
        if self.__is_only:
            self.__query.strict_outputs = True
        self.reset_intermidiates()

    def input_action(self, _):
        if self.__last_value == "?":
            # Minimize the inputs
            self.__query.maximize_objective = False
            for var in self.__last_vars:
                self.__query.objective_coefficients[var] = -1
        elif self.__last_value == "_":
            for var in self.__last_vars:
                self.__query.le_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__query.eq_constraints[var] = -int(self.__last_value)
        if self.__is_only:
            self.__query.strict_inputs = True
        self.reset_intermidiates()

    def include_action(self, _):
        if self.__last_value == "_":
            for var in self.__last_vars:
                self.__query.ge_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__query.eq_constraints[var] = self.__last_value
        if self.__is_only:
            for var in self.__last_vars:
                if var.startswith("crafter:"):
                    self.__query.strict_crafters = True
                if var.startswith("generator:"):
                    self.__query.strict_generators = True
                if var.startswith("recipe:"):
                    self.__query.strict_recipes = True
                if var.startswith("power-recipe:"):
                    self.__query.strict_power_recipes = True
        self.reset_intermidiates()

    def exclude_action(self, _):
        if self.__last_value == "_":
            for var in self.__last_vars:
                self.__query.le_constraints[var] = 0
        else:
            for var in self.__last_vars:
                self.__query.eq_constraints[var] = self.__last_value
        for var in self.__last_vars:
            self.__query.eq_constraints[var] = 0
        self.reset_intermidiates()

    def grammar(self):
        return self.__query_syntax

    def test(self, test_str):
        self.reset_intermidiates()
        self.__query = Query()
        try:
            results = self.__query_syntax.parseString(test_str, parseAll=True)
        except pp.ParseException as exception:
            print("\"" + test_str + "\" ==> failed parse:")
            print((exception.loc+1)*" " + "^")
            print(str(exception), "\n")
        else:
            print("\"" + test_str + "\" ==> parsing succeeded:\n",
                  results, "\n")
            print(self.__query)
            print()

    def parse(self, raw_query):
        self.reset_intermidiates()
        self.__query = Query()
        try:
            results = self.__query_syntax.parseString(raw_query, parseAll=True)
        except pp.ParseException as pe:
            raise QueryParseException(
                "\"" + raw_query + "\" ==> failed parse:\n" + (pe.loc+1)*" " +
                "^\n" + str(pe))
        else:
            print("\"" + raw_query + "\" ==> parsing succeeded:\n",
                  results, "\n")
            return self.__query
