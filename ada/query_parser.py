import re
from typing import List, Union, cast

import inflect
from pyparsing import (
    CaselessKeyword,
    Combine,
    Group,
    Literal,
    OneOrMore,
    Optional,
    ParseException,
    StringEnd,
    Suppress,
    Word,
    ZeroOrMore,
    alphas,
    nums,
    pyparsing_common,
    replaceWith,
)
from pyparsing.results import ParseResults

from .db.db import DB
from .db.entity import Entity
from .db.item import Item
from .help import HelpQuery
from .info import InfoQuery
from .optimization_query import Objective, OptimizationQuery
from .recipe_compare_query import RecipeCompareQuery

PRODUCE = CaselessKeyword("produce")
MAKE = CaselessKeyword("make")
CREATE = CaselessKeyword("create")
OUTPUT = CaselessKeyword("output")
FROM = CaselessKeyword("from")
INPUT = CaselessKeyword("input")
USING = CaselessKeyword("using")
WITH = CaselessKeyword("with")
WITHOUT = CaselessKeyword("without")
EXCLUDING = CaselessKeyword("excluding")
ANY = CaselessKeyword("any")
ONLY = CaselessKeyword("only")
NO = CaselessKeyword("no")
AND = CaselessKeyword("and")
OR = CaselessKeyword("or")
NOR = CaselessKeyword("nor")
POWER = CaselessKeyword("power")
TICKETS = CaselessKeyword("tickets")
SPACE = CaselessKeyword("space")
RESOURCES = CaselessKeyword("resources")
UNWEIGHTED_RESOURCES = CaselessKeyword("unweighted resources") | CaselessKeyword("unweighted-resources")
WEIGHTED_RESOURCES = CaselessKeyword("weighted resources") | CaselessKeyword("weighted-resources")
ALTERNATE_RECIPES = CaselessKeyword("alternate recipes") | CaselessKeyword("alternate-recipes")
RECIPES = CaselessKeyword("recipes")
RECIPE = CaselessKeyword("recipe")
BYPRODUCTS = CaselessKeyword("byproducts")
INGREDIENTS = CaselessKeyword("ingredients")
PRODUCTS = CaselessKeyword("products")
FOR = CaselessKeyword("for")
HELP = CaselessKeyword("help")
COMPARE = CaselessKeyword("compare")
QUESTION_MARK = Literal("?")
UNDERSCORE = Literal("_")
ZERO = Literal("0")
PLUS = Literal("+")


class QueryParseException(Exception):
    pass


class QueryParser:
    output_kw = PRODUCE | MAKE | CREATE | OUTPUT
    input_kw = FROM | INPUT
    include_kw = USING | WITH
    exclude_kw = WITHOUT | EXCLUDING

    and_kw = AND | PLUS
    or_kw = NOR | OR | AND
    unweighted_resources_kw = (RESOURCES | UNWEIGHTED_RESOURCES).setParseAction(
        replaceWith("unweighted-resources")
    )
    weighted_resources_kw = WEIGHTED_RESOURCES.setParseAction(
        replaceWith("weighted-resources")
    )
    alternate_recipes_kw = ALTERNATE_RECIPES.setParseAction(
        replaceWith("alternate-recipes")
    )

    entity_expr_end = (
            output_kw
            | input_kw
            | include_kw
            | exclude_kw
            | and_kw
            | or_kw
            | StringEnd()
    )
    entity_expr = Combine(
        OneOrMore(~entity_expr_end + Word(alphas + nums + ":.*-")),
        joinString=" ",
        adjacent=False,
    )("entity")

    # TODO: Consider allowing all literals in grammar and then enforce it during
    # validation step.
    output_literal = (POWER("power") | TICKETS)("literal")
    output_var = output_literal | entity_expr

    input_literal = (POWER | SPACE | unweighted_resources_kw | weighted_resources_kw)(
        "literal"
    )
    input_var = input_literal | entity_expr

    include_literal = SPACE("literal") | alternate_recipes_kw("literal")
    include_var = include_literal | entity_expr

    exclude_literal = alternate_recipes_kw("literal")
    byproducts = BYPRODUCTS("byproducts")
    exclude_var = exclude_literal | byproducts | entity_expr

    objective_value = QUESTION_MARK
    any_value = Optional(ANY | UNDERSCORE).setParseAction(replaceWith("_"))
    num_value = pyparsing_common.integer
    value = (objective_value | num_value | any_value)("value")

    strict = Optional(ONLY)("strict").setParseAction(lambda t: len(t) != 0)

    output_expr = Group(strict + value + output_var)
    input_expr = Group(strict + value + input_var)
    # includes are always strict
    include_expr = Group(Optional(ONLY) + include_var)
    exclude_expr = Group(exclude_var)

    outputs = output_expr + ZeroOrMore(Suppress(and_kw) + output_expr)
    inputs = input_expr + ZeroOrMore(Suppress(and_kw) + input_expr)
    includes = include_expr + ZeroOrMore(Suppress(and_kw) + include_expr)
    excludes = exclude_expr + ZeroOrMore(Suppress(or_kw) + exclude_expr)

    outputs_expr = (Suppress(output_kw) + outputs)("outputs")
    inputs_expr = Optional(Suppress(input_kw) + inputs)("inputs")
    includes_expr = Optional(Suppress(include_kw) + includes)("includes")
    excludes_expr = Optional(Suppress(exclude_kw) + excludes)("excludes")

    optimization_query = (outputs_expr + inputs_expr + includes_expr + excludes_expr)(
        "optimization"
    )

    entity_query = entity_expr("entity-details")

    single_recipe_query = (Suppress(RECIPE) + entity_expr)("single-recipe")

    recipe_for_query = (
            (Suppress(RECIPE + FOR) + entity_expr) | (entity_expr + Suppress(RECIPE))
    )("recipe-for")

    recipes_for_query = (
            (Suppress(RECIPES + FOR) + entity_expr) | (entity_expr + Suppress(RECIPES))
    )("recipes-for")

    recipes_from_kw = FROM | USING | WITH
    recipes_from_query = (Suppress(RECIPES + recipes_from_kw) + entity_expr)(
        "recipes-from"
    )

    recipe_query = (
            recipes_for_query | recipe_for_query | recipes_from_query | single_recipe_query
    )

    ingredients_for_query = (
            (Suppress(INGREDIENTS + FOR) + entity_expr) | (entity_expr + Suppress(INGREDIENTS))
    )("ingredients-for")

    products_for_query = (
            (Suppress(PRODUCTS + FOR) + entity_expr) | (entity_expr + Suppress(PRODUCTS))
    )("products-for")

    help_query = HELP("help")

    compare_recipe_query = (
            Suppress(COMPARE + RECIPES + FOR)
            + entity_expr
            + Optional(WITH + ALTERNATE_RECIPES)("include-alternates")
    )("recipe-compare")

    query_grammar = (
            help_query
            ^ optimization_query
            ^ recipe_query
            ^ compare_recipe_query
            ^ ingredients_for_query
            ^ products_for_query
            ^ entity_query
    )

    def __init__(self, db: DB) -> None:
        self._db = db

    @staticmethod
    def _check_var(
            expr: str, var: Entity
    ) -> bool:
        # Support the following:
        # 1. singular human-readable name
        # 2. plural human-readable name
        # 3. var name
        # 4. regex on human-readable name
        # 5. regex on var name
        expr = expr.strip().lower()
        expr_parts = list(filter(None, re.split(r"[\s\-_:]", expr)))

        singular = var.human_readable_name().lower()
        singular_parts = list(filter(None, re.split(r"[\s:\-]", singular)))
        if expr_parts == singular_parts:
            return True
        plural = inflect.engine().plural(singular)
        plural_parts = list(filter(None, re.split(r"[\s:\-]", plural)))
        if expr_parts == plural_parts:
            return True
        if singular.startswith("recipe: alternate: "):
            if expr_parts == singular_parts[2:]:
                return True
            if expr_parts == singular_parts[:1] + singular_parts[2:]:
                return True
            if expr_parts == plural_parts[2:]:
                return True
            if expr_parts == plural_parts[:1] + plural_parts[2:]:
                return True
        var_parts = list(filter(None, re.split(r"[:\-]", var.var())))
        if expr_parts == var_parts:
            return True
        # Don't require the user to specify the entity type.
        typeless_var = var.var().split(":", 1)[1]
        typeless_var_parts = re.split(r"[:\-]", typeless_var)
        if expr_parts == typeless_var_parts:
            return True

        return (
                re.fullmatch(expr, singular) is not None
                or re.fullmatch(expr, plural) is not None
                or re.fullmatch(expr, var.var()) is not None
                or re.fullmatch(expr, typeless_var) is not None
        )

    def _get_matches(
            self, expr: str, allowed_types: List[str]
    ) -> list[Entity]:
        allowed_vars = set()
        if "resource" in allowed_types:
            allowed_vars.update(
                [item for item in self._db.items().values() if item.is_resource()]
            )
        if "item" in allowed_types:
            allowed_vars.update(
                [item for item in self._db.items().values() if not item.is_resource()]
            )
        if "recipe" in allowed_types:
            allowed_vars.update(recipe for recipe in self._db.recipes().values())
        if "power-recipe" in allowed_types:
            allowed_vars.update(recipe for recipe in self._db.power_recipes().values())
        if "crafter" in allowed_types:
            allowed_vars.update(crafter for crafter in self._db.crafters().values())
        if "extractor" in allowed_types:
            allowed_vars.update(extractor for extractor in self._db.extractors().values())
        if "generator" in allowed_types:
            allowed_vars.update(generator for generator in self._db.generators().values())
        return [var for var in allowed_vars if QueryParser._check_var(expr, var)]

    def _parse_outputs(self, outputs: ParseResults, query: OptimizationQuery) -> None:
        if not outputs:
            raise QueryParseException("No outputs specified in optimization query.")
        for output in outputs:
            output_vars = []
            if "literal" in output:
                output_vars = [output["literal"]]
            if "entity" in output:
                output_vars.extend(
                    [var.var() for var in self._get_matches(output["entity"], ["item"])]
                )
                if len(output_vars) == 0:
                    raise QueryParseException(
                        "Could not parse item expression '" + output["entity"] + "'."
                    )
            strict = output["strict"]
            value = output["value"]
            for output_var in output_vars:
                if value == "?":
                    if query.has_objective():
                        raise QueryParseException("Only one objective may be specified.")
                    query.add_objective(Objective(output_var, True, 1))
                else:
                    amount = None if value == "_" else int(value)
                    query.add_output(output_var, amount, strict)

    def _parse_inputs(self, inputs: ParseResults, query: OptimizationQuery) -> None:
        if not inputs:
            return
        for input_ in inputs:
            input_vars = []
            if "literal" in input_:
                input_vars = [input_["literal"]]
            elif "entity" in input_:
                input_vars.extend([var.var() for var in self._get_matches(input_["entity"], ["resource", "item"])])
                if len(input_vars) == 0:
                    raise QueryParseException(
                        "Could not parse resource or item expression '"
                        + input_["entity"]
                        + "'."
                    )
            strict = input_["strict"]
            value = input_["value"]
            for input_var in input_vars:
                if value == "?":
                    if query.has_objective():
                        raise QueryParseException("Only one objective may be specified.")
                    query.add_objective(Objective(input_var, False, -1))
                else:
                    amount = None if value == "_" else int(value)
                    query.add_input(input_var, -amount, strict)

    def _parse_includes(self, includes: ParseResults, query: OptimizationQuery) -> None:
        if not includes:
            return
        for include in includes:
            include_vars = []
            if "literal" in include:
                include_vars = [include["literal"]]
            elif "entity" in include:
                include_vars.extend(
                    [
                        var.var()
                        for var in self._get_matches(
                        include["entity"],
                        [
                            "recipe",
                            "power-recipe",
                            "crafter",
                            "extractor",
                            "generator",
                        ],
                    )
                    ]
                )
                if len(include_vars) == 0:
                    raise QueryParseException(
                        "Could not parse recipe, power recipe, crafter, or generator expression '"
                        + include["entity"]
                        + "'."
                    )
            for include_var in include_vars:
                query.add_include(include_var)

    def _parse_excludes(self, excludes: ParseResults, query: OptimizationQuery) -> None:
        if not excludes:
            return
        for exclude in excludes:
            exclude_vars = []
            if "literal" in exclude:
                exclude_vars = [exclude["literal"]]
            elif "entity" in exclude:
                exclude_vars.extend(
                    [
                        var.var()
                        for var in self._get_matches(
                        exclude["entity"],
                        [
                            "recipe",
                            "power-recipe",
                            "crafter",
                            "extractor",
                            "generator",
                        ],
                    )
                    ]
                )
                if len(exclude_vars) == 0:
                    raise QueryParseException(
                        "Could not parse recipe, power recipe, crafter, or generator expression '"
                        + exclude["entity"]
                        + "'."
                    )

            if "byproducts" in exclude:
                query.set_strict_outputs(True)
            for exclude_var in exclude_vars:
                query.add_exclude(exclude_var)

    def _parse_optimization_query(
            self, raw_query: str, parse_results: ParseResults
    ) -> OptimizationQuery:
        query = OptimizationQuery()
        self._parse_outputs(parse_results.get("outputs"), query)
        self._parse_inputs(parse_results.get("inputs"), query)
        self._parse_includes(parse_results.get("includes"), query)
        self._parse_excludes(parse_results.get("excludes"), query)
        if not query.has_objective():
            query.add_objective(Objective("unweighted-resources", False, -1))
        return query

    def _parse_recipe_for_query(self, raw_query, parse_results):
        query = InfoQuery(raw_query)
        matches = self._get_matches(
            parse_results.get("entity"),
            ["item", "crafter", "extractor", "generator"],
        )
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse item expression '" + parse_results.get("entity") + "'."
            )
        all_vars = []
        non_alternate_vars = []
        for match in matches:
            var = match.var()
            for recipe in self._db.recipes_for_product(var):
                all_vars.append(recipe)
                if not recipe.is_alternate():
                    non_alternate_vars.append(recipe)
        if len(non_alternate_vars) > 0:
            query.vars.extend(non_alternate_vars)
        else:
            query.vars.extend(all_vars)
        return query

    def _parse_recipes_for_query(self, raw_query, parse_results):
        query = InfoQuery(raw_query)
        matches = self._get_matches(
            parse_results.get("entity"),
            ["resource", "item", "crafter", "extractor", "generator"],
        )
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse resource, item, crafter, or generator expression '"
                + parse_results.get("entity")
                + "'."
            )
        for match in matches:
            var = match.var()
            if var.startswith("item") or var.startswith("resource"):
                for recipe in self._db.recipes_for_product(var):
                    query.vars.append(recipe)
            elif var.startswith("crafter"):
                for recipe in self._db.recipes().values():
                    if not recipe.is_craftable_in_building():
                        continue
                    if recipe.crafter().var() == var:
                        query.vars.append(recipe)
            elif var.startswith("generator"):
                for power_recipe in self._db.power_recipes().values():
                    if power_recipe.generator().var() == var:
                        query.vars.append(power_recipe)
        return query

    def _parse_recipes_from_query(self, raw_query, parse_results):
        query = InfoQuery(raw_query)
        matches = self._get_matches(parse_results.get("entity"), ["resource", "item"])
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse resource or item expression '"
                + parse_results.get("entity")
                + "'."
            )
        for match in matches:
            for recipe in self._db.recipes_for_ingredient(match.var()):
                query.vars.append(recipe)
        return query

    def _parse_single_recipe_query(self, raw_query, parse_results):
        query = InfoQuery(raw_query)
        matches = self._get_matches(
            parse_results.get("entity"), ["recipe"]
        )
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse recipe expression '"
                + parse_results.get("entity")
                + "'."
            )
        query.vars.extend(matches)
        return query

    def _parse_recipe_compare_query(
            self, raw_query: str, parse_results: ParseResults
    ) -> RecipeCompareQuery:
        query = RecipeCompareQuery(raw_query)
        matches = self._get_matches(parse_results.get("entity"), ["item"])
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse compare recipes for expression '"
                + parse_results.get("entity")
                + "'."
            )
        elif len(matches) > 1:
            raise QueryParseException(
                "Multiple items were matched:\n   "
                + "\n   ".join([match.human_readable_name() for match in matches])
                + "\nPlease repeat the command with a more specific item name."
            )
        product_item: Item = cast(Item, matches[0])
        related_recipes = list(self._db.recipes_for_product(product_item.var()))
        base_recipe = None
        if len(related_recipes) == 0:
            raise QueryParseException(
                "Could not find any recipe that produces "
                + product_item.human_readable_name()
            )
        elif len(related_recipes) == 1:
            base_recipe = related_recipes[0]
            related_recipes.clear()
        else:
            for recipe in list(related_recipes):
                if recipe.slug() == product_item.slug():
                    base_recipe = recipe
                    related_recipes.remove(recipe)
                    break
            if base_recipe is None:
                raise QueryParseException(
                    "Could not find base recipe for "
                    + product_item.human_readable_name()
                )

        query.product_item = product_item
        query.base_recipe = base_recipe
        query.related_recipes = related_recipes
        query.include_alternates = "include-alternates" in parse_results
        return query

    def _parse_ingredients_for_query(self, raw_query, parse_results):
        query = InfoQuery(raw_query)
        matches = self._get_matches(
            parse_results.get("entity"),
            ["recipe", "power-recipe"],
        )
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse resource or item expression '"
                + parse_results.get("entity")
                + "'."
            )
        for match in matches:
            var = match.var()
            if var.startswith("recipe"):
                if var in self._db.recipes():
                    recipe = self._db.recipes()[var]
                    for ingredient in recipe.ingredients().values():
                        query.vars.append(ingredient.item())
            elif var.startswith("power-recipe"):
                if var in self._db.power_recipes():
                    power_recipe = self._db.power_recipes()[var]
                    query.vars.append(power_recipe.fuel_item())
        return query

    def _parse_products_for_query(self, raw_query, parse_results):
        query = InfoQuery(raw_query)
        matches = self._get_matches(
            parse_results.get("entity"),
            ["recipe"],
        )
        if len(matches) == 0:
            raise QueryParseException(
                "Could not parse resource or item expression '"
                + parse_results.get("entity")
                + "'."
            )
        for match in matches:
            var = match.var()
            if var.startswith("recipe"):
                if var in self._db.recipes():
                    recipe = self._db.recipes()[var]
                    for product in recipe.products().values():
                        query.vars.append(product.item())
        return query

    def _parse_entity_details(
            self, raw_query: str, parse_results: ParseResults
    ) -> InfoQuery:
        query = InfoQuery(raw_query)
        non_recipe_matches = self._get_matches(
            parse_results.get("entity-details"),
            ["resource", "item", "crafter", "extractor", "generator"],
        )
        if len(non_recipe_matches) > 0:
            query.vars.extend(non_recipe_matches)
            return query
        recipe_matches = self._get_matches(
            parse_results.get("entity-details"),
            ["recipe", "power-recipe"],
        )
        if len(recipe_matches) == 0:
            raise QueryParseException(
                "Could not parse entity expression '"
                + parse_results.get("entity-details")
                + "'."
            )
        query.vars.extend(recipe_matches)
        return query

    def parse(
            self, raw_query: str
    ) -> Union[InfoQuery, HelpQuery, RecipeCompareQuery, OptimizationQuery]:
        try:
            results = QueryParser.query_grammar.parseString(raw_query, parseAll=True)
        except ParseException as pe:
            raise QueryParseException(
                '"'
                + raw_query
                + '" ==> failed parse:\n'
                + (pe.loc + 1) * " "
                + "^\n"
                + str(pe)
            )

        # print("\"" + raw_query + "\" ==> parsing succeeded:\n",
        #       results, "\n", results.dump(), "\n")

        if "help" in results:
            return HelpQuery()
        elif "optimization" in results:
            return self._parse_optimization_query(raw_query, results)
        elif "single-recipe" in results:
            return self._parse_single_recipe_query(raw_query, results)
        elif "recipe-for" in results:
            return self._parse_recipe_for_query(raw_query, results)
        elif "recipes-for" in results:
            return self._parse_recipes_for_query(raw_query, results)
        elif "recipes-from" in results:
            return self._parse_recipes_from_query(raw_query, results)
        elif "recipe-compare" in results:
            return self._parse_recipe_compare_query(raw_query, results)
        elif "ingredients-for" in results:
            return self._parse_ingredients_for_query(raw_query, results)
        elif "products-for" in results:
            return self._parse_products_for_query(raw_query, results)
        elif "entity-details" in results:
            return self._parse_entity_details(raw_query, results)
        else:
            raise QueryParseException("Unknown query.")
