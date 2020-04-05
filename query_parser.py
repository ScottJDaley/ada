from pyparsing import (
    CaselessKeyword,
    Literal,
    Word,
    alphas,
    NotAny,
    SkipTo,
    Optional,
    pyparsing_common,
    replaceWith,
    Group,
    ZeroOrMore,
    OneOrMore,
    Suppress,
    StringEnd,
    White,
    Combine,
)
# TODO: Remove this
import pyparsing as pp
from pyparsing import pyparsing_common as ppc
import inflect
from functools import partial
from query import OptimizationQuery, InfoQuery
import re

# keywords = {
#     k + "_": pp.CaselessKeyword(k)
#     for k in """
#         produce make create output from input using with without
#         excluding any only no and or nor power tickets space unweighted
#         weighted resources alterante recipes recipe byproducts for
#     """.split()
# }
# vars().update(keywords)
PRODUCE = CaselessKeyword('produce')
MAKE = CaselessKeyword('make')
CREATE = CaselessKeyword('create')
OUTPUT = CaselessKeyword('output')
FROM = CaselessKeyword('from')
INPUT = CaselessKeyword('input')
USING = CaselessKeyword('using')
WITH = CaselessKeyword('with')
WITHOUT = CaselessKeyword('without')
EXCLUDING = CaselessKeyword('excluding')
ANY = CaselessKeyword('any')
ONLY = CaselessKeyword('only')
NO = CaselessKeyword('no')
AND = CaselessKeyword('and')
OR = CaselessKeyword('or')
NOR = CaselessKeyword('nor')
POWER = CaselessKeyword('power')
TICKETS = CaselessKeyword('tickets')
SPACE = CaselessKeyword('space')
RESOURCES = CaselessKeyword('resources')
UNWEIGHTED_RESOURCES = CaselessKeyword('unweighted resources')
WEIGHTED_RESOURCES = CaselessKeyword('weighted resources')
ALTERNATE_RECIPES = CaselessKeyword('alternate recipes')
RECIPES = CaselessKeyword('recipes')
RECIPE = CaselessKeyword('recipe')
BYPRODUCTS = CaselessKeyword('byproducts')
FOR = CaselessKeyword('for')
QUESTION_MARK = Literal('?')
UNDERSCORE = Literal('_')
ZERO = Literal('0')
PLUS = Literal('+')


class QueryParseException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class QueryParser:

    output_kw = PRODUCE | MAKE | CREATE | OUTPUT
    input_kw = FROM | INPUT
    include_kw = USING | WITH
    exclude_kw = WITHOUT | EXCLUDING

    and_kw = AND | PLUS
    or_kw = NOR | OR | AND
    unweighted_resources_kw = (RESOURCES | UNWEIGHTED_RESOURCES).setParseAction(
        replaceWith("unweighted-resources"))
    weighted_resources_kw = WEIGHTED_RESOURCES.setParseAction(
        replaceWith("weighted-resources"))
    alternate_recipes_kw = ALTERNATE_RECIPES.setParseAction(
        replaceWith("alternate-recipes"))

    entity_expr_end = (output_kw | input_kw | exclude_kw |
                       and_kw | or_kw | RECIPE | RECIPES | StringEnd())
    entity_expr = Combine(SkipTo(entity_expr_end))("entity")

    # TODO: Consider allowing all literals in grammar and then enforce it during
    # validation step.
    output_literal = (POWER | TICKETS)("literal")
    output_var = output_literal | entity_expr

    input_literal = (
        POWER | SPACE | unweighted_resources_kw | weighted_resources_kw)("literal")
    input_var = input_literal | entity_expr

    include_literal = SPACE("literal")
    include_var = include_literal | entity_expr

    exclude_literal = (alternate_recipes_kw | BYPRODUCTS)("literal")
    exclude_var = exclude_literal | entity_expr

    objective_value = QUESTION_MARK
    any_value = Optional(ANY | UNDERSCORE).setParseAction(replaceWith('_'))
    num_value = pyparsing_common.integer
    value = (objective_value | num_value | any_value)("value")

    strict = Optional(ONLY)("strict").setParseAction(lambda t: len(t) != 0)

    output_expr = Group(strict + value + output_var)
    input_expr = Group(strict + value + input_var)
    # includes are always strict
    include_expr = Group(Optional(ONLY) + include_var)
    exclude_expr = Group(exclude_var)

    outputs = (
        output_expr + ZeroOrMore(Suppress(and_kw) + output_expr)
    )
    inputs = (
        input_expr + ZeroOrMore(Suppress(and_kw) + input_expr)
    )
    includes = (
        include_expr + ZeroOrMore(Suppress(and_kw) + include_expr)
    )
    excludes = (
        exclude_expr + ZeroOrMore(Suppress(or_kw) + exclude_expr)
    )

    outputs_expr = (Suppress(output_kw) + outputs)("outputs")
    inputs_expr = Optional(Suppress(input_kw) + inputs)("inputs")
    includes_expr = Optional(Suppress(include_kw) + includes)("includes")
    excludes_expr = Optional(Suppress(exclude_kw) + excludes)("excludes")

    optimization_query = (
        outputs_expr + inputs_expr + includes_expr + excludes_expr
    )("optimization")

    entity_query = entity_expr("entity")

    item_recipe_query = (entity_expr + Suppress(RECIPE))("item-recipe")

    recipes_for_query = (
        (entity_expr + Suppress(RECIPES))
        | (Suppress(RECIPES + FOR) + entity_expr)
    )("recipes-for")

    recipes_from_kw = FROM | USING | WITH
    recipes_from_query = (
        Suppress(RECIPES + recipes_from_kw) + entity_expr
    )("recipes-from")

    recipe_query = item_recipe_query | recipes_for_query | recipes_from_query

    query = optimization_query | recipe_query | entity_query

    def __init__(self, db):
        self._db = db

    @staticmethod
    def _check_var(expr, var):
        # Support the following:
        # 1. singular human-readable name
        # 2. plural human-readable name
        # 3. var name
        # 4. regex on human-readable name
        # 5. regex on var name
        expr = expr.strip().lower()
        expr_parts = re.split(r'[\s\-\_:]', expr)

        singular = var.human_readable_name().lower()
        singular_parts = re.split(r'[\s:]', singular)
        if expr_parts == singular_parts:
            return True
        plural = inflect.engine().plural(singular)
        plural_parts = re.split(r'[\s:]', plural)
        if expr_parts == plural_parts:
            return True

        var_parts = re.split(r'[:\-]', var.var())
        if expr_parts == var_parts:
            return True
        # Don't require the user to specify the entity type.
        if expr_parts == var_parts[1:]:
            return True

        if re.fullmatch(expr, singular):
            return True
        if re.fullmatch(expr, plural):
            return True
        if re.fullmatch(expr, var.var()):
            return True
        return False

    def _get_matches(self, expr, allowed_types):
        print("get_matches '" + expr + "'", allowed_types)
        allowed_vars = set()
        if "resource" in allowed_types:
            allowed_vars.update(
                [item for item in self._db.items().values() if item.is_resource()])
        if "item" in allowed_types:
            allowed_vars.update(
                [item for item in self._db.items().values() if not item.is_resource()])
        if "recipe" in allowed_types:
            allowed_vars.update(self._db.recipes().values())
        if "power-recipe" in allowed_types:
            allowed_vars.update(self._db.power_recipes().values())
        if "crafter" in allowed_types:
            allowed_vars.update(self._db.crafters().values())
        if "generator" in allowed_types:
            allowed_vars.update(self._db.generators().values())
        return [var.var() for var in allowed_vars if QueryParser._check_var(expr, var)]

    def _build_optimization_query(self, parse_results):
        print("_build_optimization_query()")
        if not parse_results.get("outputs"):
            raise QueryParseException(
                "No outputs specified in optimization query.")
        if not parse_results.get("inputs"):
            # TODO: Default to ? unweighted-resources for input
            raise QueryParseException(
                "No inputs specified in optimization query.")

        query = OptimizationQuery()
        found_objective = False
        for output in parse_results.get("outputs"):
            output_vars = []
            if "literal" in output:
                output_vars = [output["literal"]]
            if "entity" in output:
                output_vars.extend(self._get_matches(
                    output["entity"], ["item"]))
            value = output["value"]
            if value == "?":
                if found_objective:
                    raise QueryParseException(
                        "Only one objective may be specified.")
                found_objective = True
                query.maximize_objective = True
                query.objective_coefficients = {var: 1 for var in output_vars}
            elif value == "_":
                query.ge_constraints.update({var: 0 for var in output_vars})
            else:
                query.ge_constraints.update({var: value for var in output_vars})
            if output["strict"]:
                query.strict_outputs = True
        for input_ in parse_results.get("inputs"):
            input_vars = []
            if "literal" in input_:
                input_vars = [input_["literal"]]
            elif "entity" in input_:
                input_vars.extend(self._get_matches(
                    input_["entity"],
                    ["resource", "item"]))
            value = input_["value"]
            if value == "?":
                if found_objective:
                    raise QueryParseException(
                        "Only one objective may be specified.")
                found_objective = True
                query.maximize_objective = False
                query.objective_coefficients = {var: -1 for var in input_vars}
            elif value == "_":
                query.le_constraints.update({var: 0 for var in input_vars})
            else:
                query.ge_constraints.update({var: -value for var in input_vars})
            if input_["strict"]:
                query.strict_inputs = True
        if parse_results.get("includes"):
            for include in parse_results.get("includes"):
                include_vars = []
                if "literal" in include:
                    include_vars = [include["literal"]]
                elif "entity" in include:
                    include_vars.extend(self._get_matches(
                        include["entity"],
                        ["recipe", "power-recipe", "crafter", "generator"]))
                query.ge_constraints.update({var: 0 for var in include_vars})
                for var in include_vars:
                    if var.startswith("recipe:"):
                        query.strict_recipes = True
                    if var.startswith("power-recipe:"):
                        query.strict_power_recipes = True
                    if var.startswith("crafter:"):
                        query.strict_crafters = True
                    if var.startswith("generator:"):
                        query.strict_generators = True
        if parse_results.get("excludes"):
            for exclude in parse_results.get("excludes"):
                exclude_vars = []
                if "literal" in exclude:
                    exclude_vars = [exclude["literal"]]
                elif "entity" in exclude:
                    exclude_vars.extend(self._get_matches(
                        exclude["entity"],
                        ["recipe", "power-recipe", "crafter", "generator"]))
                query.eq_constraints.update({var: 0 for var in exclude_vars})

        return query

    def _build_info_query(self, parse_results):
        print("_build_info_query")

    def parse(self, raw_query):
        try:
            results = QueryParser.query.parseString(raw_query, parseAll=True)
        except pp.ParseException as pe:
            raise QueryParseException(
                "\"" + raw_query + "\" ==> failed parse:\n" + (pe.loc+1)*" " +
                "^\n" + str(pe))

        print("\"" + raw_query + "\" ==> parsing succeeded:\n",
              results, "\n", results.dump(), "\n")

        if "optimization" in results:
            return self._build_optimization_query(results)
        elif "info" in results:
            return self._build_info_query(results)

    # self.__inflect = inflect.engine()

    # keywords = {
    #     k + "_": pp.CaselessKeyword(k)
    #     for k in """
    #         produce make create output from input using with without
    #         excluding any only no and or nor power tickets space unweighted
    #         weighted resources alterante recipes recipe byproducts for
    #     """.split()
    # }
    # vars().update(keywords)

    # Keywords
    # output_kw = pp.Keyword("produce") | pp.Keyword(
    #     "make") | pp.Keyword("create") | pp.Keyword("output")
    # input_kw = pp.Keyword("from") | pp.Keyword(
    #     "input") | pp.Keyword("using") | pp.Keyword("with")
    # exclude_kw = pp.Keyword("without") | pp.Keyword("excluding")

    # objective_kw = pp.Keyword("?")
    # any_kw = (pp.Keyword("any") | pp.Keyword("_")
    #           ).setParseAction(partial(self.as_literal, "_"))
    # only_kw = pp.Keyword("only").setParseAction(self.set_is_only)
    # no_kw = (pp.Keyword("no") | pp.Keyword("0") |
    #          "-").setParseAction(partial(self.as_literal, 0))
    # and_kw = (pp.Keyword("and") | "+").suppress()
    # nor_kw = (pp.Keyword("and") | pp.Keyword(
    #     "or") | pp.Keyword("nor")).suppress()
    # power_kw = pp.Keyword("power").setParseAction(
    #     partial(self.as_literal, "power"))
    # tickets_kw = pp.Keyword("tickets").setParseAction(
    #     partial(self.as_literal, "tickets"))
    # space_kw = pp.Keyword("space").setParseAction(
    #     partial(self.as_literal, "space"))
    # unweighted_resources_kw = (pp.Keyword("unweighted resources") | pp.Keyword(
    #     "resources")).setParseAction(partial(self.as_literal, "unweighted-resources"))
    # weighted_resources_kw = pp.Keyword("weighted resources").setParseAction(
    #     partial(self.as_literal, "weighted-resources"))
    # alternate_recipes_kw = pp.Keyword("alternate recipes").setParseAction(
    #     partial(self.as_literal, "alternate-recipes"))
    # byproducts_kw = pp.Keyword("byproducts").setParseAction(
    #     partial(self.as_literal, "byproducts"))
    # recipe_kw = pp.CaselessKeyword("recipe")
    # recipes_kw = pp.CaselessKeyword("recipes")
    # for_kw = pp.CaselessKeyword("for")

    # end_of_expr = output_kw | input_kw | include_kw | exclude_kw | and_kw

    # Expressions for variable names
    # Consider going back to looking for any string up until end_of_expr.
    # Then as a parse action, check if it matches. That way we can give a
    # better failure message.
    # item_expr = self.get_var_expr(
    #     [item for item in db.items().values() if not item.is_resource()])
    # resource_expr = self.get_var_expr(
    #     [item for item in db.items().values() if item.is_resource()])
    # recipe_expr = self.get_var_expr(db.recipes().values())
    # power_recipe_expr = self.get_var_expr(db.power_recipes().values())
    # crafter_expr = self.get_var_expr(db.crafters().values())
    # generator_expr = self.get_var_expr(db.generators().values())

    # output_var = (power_kw | tickets_kw | item_expr)("var")
    # input_var = (power_kw | space_kw | recipe_expr | power_recipe_expr
    #              | crafter_expr | generator_expr | unweighted_resources_kw
    #              | weighted_resources_kw | resource_expr | item_expr)("var")
    # exclude_var = (alternate_recipes_kw | byproducts_kw | recipe_expr
    #                | power_recipe_expr | crafter_expr | generator_expr)("var")

    # number_value = ppc.integer
    # value = number_value | any_kw | objective_kw | no_kw
    # value_expr = pp.Optional(value)("value")

    # output_expr = pp.Group(pp.Optional(value_expr) + output_var)("output*")
    # input_expr = pp.Group(pp.Optional(value_expr) + input_var)("input*")
    # exclude_expr = exclude_var("exclude*")

    # outputs = pp.Group(pp.Optional(only_kw) + output_expr +
    #                    pp.ZeroOrMore(and_kw + output_expr))
    # inputs = pp.Group(pp.Optional(only_kw) + input_expr +
    #                   pp.ZeroOrMore(and_kw + input_expr))
    # excludes = pp.Group(
    #     exclude_expr + pp.ZeroOrMore(nor_kw + exclude_expr))

    # outputs_expr = output_kw + outputs
    # inputs_expr = input_kw + inputs
    # excludes_expr = exclude_kw + excludes

    # optimization_query = (outputs_expr + pp.Optional(inputs_expr)
    #                       + pp.Optional(excludes_expr))("optimization")

    # item_query = (resource_expr | item_expr)("item")
    # crafter_query = crafter_expr("crafter")
    # generator_query = generator_expr("generator")

    # recipes_for_query = ((item_expr + recipes_kw) | (item_expr + recipe_kw)
    #                      | (recipes_kw + for_kw + item_expr)
    #                      | (recipe_kw + for_kw + item_expr))("recipes-for")
    # recipes_from_query = (recipes_kw + input_kw +
    #                       item_expr)("recipes-from")
    # single_recipe_query = recipe_expr("recipe")
    # crafter_recipes_query = (
    #     crafter_expr + recipes_kw)("crafter-recipes")
    # generator_recipes_query = (
    #     generator_expr + recipes_kw)("generator-recipes")

    # recipe_query = (recipes_for_query | recipes_from_query |
    #                 single_recipe_query | crafter_recipes_query |
    #                 generator_recipes_query)

    # info_query = (recipe_query | item_query |
    #               crafter_query | generator_query)("info")

    # self.__query_syntax = optimization_query | info_query

    # self.__is_optimization_query = output_kw

    # self.__last_vars = []
    # self.__last_value = None
    # self.__is_only = False
    # self.__query = None

    # def reset_intermidiates(self):
    #     self.__last_vars = []
    #     self.__last_value = None
    #     self.__is_only = False

    # def push_number_value(self, toks):
    #     self.__last_value = toks[0]

    # def push_value(self, value, _):
    #     self.__last_value = value

    # def set_is_only(self, _):
    #     self.__is_only = True

    # def handle_value(self, _):
    #     if not self.__last_value:
    #         self.__last_value = "_"

    # def push_var(self, var, _):
    #     self.__last_vars.append(var)
    #     print(var)

    # def get_var_expr(self, vars):
    #     var_names = []
    #     for var in vars:
    #         singular = pp.CaselessLiteral(var.human_readable_name().lower())
    #         plural = pp.CaselessLiteral(
    #             self.__inflect.plural(var.human_readable_name().lower()))
    #         var_names.append((plural | singular).setParseAction(
    #             partial(self.as_literal, var.var())))
    #     return pp.Or(var_names)

    # def as_literal(self, var, __):
    #     return var

    # def output_action(self, _):
    #     print("output_action()")
    #     if self.__last_value == "?":
    #         # Maximize the outputs
    #         self.__query.maximize_objective = True
    #         for var in self.__last_vars:
    #             self.__query.objective_coefficients[var] = 1
    #     elif self.__last_value == "_":
    #         for var in self.__last_vars:
    #             self.__query.ge_constraints[var] = 0
    #     else:
    #         for var in self.__last_vars:
    #             self.__query.eq_constraints[var] = int(self.__last_value)
    #     if self.__is_only:
    #         self.__query.strict_outputs = True
    #     self.reset_intermidiates()

    # def input_action(self, _):
    #     if self.__last_value == "?":
    #         # Minimize the inputs
    #         self.__query.maximize_objective = False
    #         for var in self.__last_vars:
    #             self.__query.objective_coefficients[var] = -1
    #     elif self.__last_value == "_":
    #         for var in self.__last_vars:
    #             self.__query.le_constraints[var] = 0
    #     else:
    #         for var in self.__last_vars:
    #             self.__query.eq_constraints[var] = -int(self.__last_value)
    #     if self.__is_only:
    #         self.__query.strict_inputs = True
    #     self.reset_intermidiates()

    # def include_action(self, _):
    #     if self.__last_value == "_":
    #         for var in self.__last_vars:
    #             self.__query.ge_constraints[var] = 0
    #     else:
    #         for var in self.__last_vars:
    #             self.__query.eq_constraints[var] = self.__last_value
    #     if self.__is_only:
    #         for var in self.__last_vars:
    #             if var.startswith("crafter:"):
    #                 self.__query.strict_crafters = True
    #             if var.startswith("generator:"):
    #                 self.__query.strict_generators = True
    #             if var.startswith("recipe:"):
    #                 self.__query.strict_recipes = True
    #             if var.startswith("power-recipe:"):
    #                 self.__query.strict_power_recipes = True
    #     self.reset_intermidiates()

    # def exclude_action(self, _):
    #     if self.__last_value == "_":
    #         for var in self.__last_vars:
    #             self.__query.le_constraints[var] = 0
    #     else:
    #         for var in self.__last_vars:
    #             self.__query.eq_constraints[var] = self.__last_value
    #     for var in self.__last_vars:
    #         self.__query.eq_constraints[var] = 0
    #     self.reset_intermidiates()

    # def push_info_vars(self, toks):
    #     print("push_info_vars", toks, self.__last_vars)
    #     self.__query.vars.extend(self.__last_vars)

    # def recipes_for_action(self, _):
    #     for var in self.__last_vars:
    #         for recipe in self.__db.recipes_for_product(var):
    #             self.__query.vars.append(recipe.var())

    # def recipes_from_action(self, _):
    #     for var in self.__last_vars:
    #         for recipe in self.__db.recipes_for_ingredient(var):
    #             self.__query.vars.append(recipe.var())

    # def crafter_recipes(self, toks):
    #     print("crafter recipes", toks, self.__last_vars)
    #     for var in self.__last_vars:
    #         for recipe in self.__db.recipes().values():
    #             if recipe.crafter().var() == var:
    #                 self.__query.vars.append(recipe.var())

    # def generator_recipes(self, _):
    #     for var in self.__last_vars:
    #         for power_recipe in self.__db.power_recipes().values():
    #             if power_recipe.generator().var() == var:
    #                 self.__query.vars.append(power_recipe.var())

    # def grammar(self):
    #     return self.__query_syntax

    # def test(self, test_str):
    #     self.reset_intermidiates()
    #     self.__query = OptimizationQuery()
    #     try:
    #         results = self.__query_syntax.parseString(test_str, parseAll=True)
    #     except pp.ParseException as exception:
    #         print("\"" + test_str + "\" ==> failed parse:")
    #         print((exception.loc+1)*" " + "^")
    #         print(str(exception), "\n")
    #     else:
    #         print("\"" + test_str + "\" ==> parsing succeeded:\n",
    #               results, "\n")
    #         print(self.__query)
    #         print()

    # def parse(self, raw_query):
    #     self.reset_intermidiates()
    #     # TODO: Use parse actions and supress() to convert and normalize input.
    #     # Let parser return the AST and derive the query from that instead of
    #     # building it using parse actions
    #     try:
    #         self.__is_optimization_query.parseString(raw_query, parseAll=False)
    #     except pp.ParseException as pe:
    #         self.__query = InfoQuery()
    #         print("Found info query")
    #     else:
    #         self.__query = OptimizationQuery()
    #         print("Found optimization query")

    #     try:
    #         results = self.__query_syntax.parseString(raw_query, parseAll=True)
    #     except pp.ParseException as pe:
    #         raise QueryParseException(
    #             "\"" + raw_query + "\" ==> failed parse:\n" + (pe.loc+1)*" " +
    #             "^\n" + str(pe))
    #     else:
    #         print("\"" + raw_query + "\" ==> parsing succeeded:\n",
    #               results, "\n", results.dump(), "\n")
    #         return self.__query
