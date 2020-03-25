from db import DB
from optimizer import Optimizer
from query_parser import QueryParser, ParseException


class ItemsResult:
    def __init__(self, items, normalized_args):
        self.items = items
        self.normalized_args = normalized_args


class RecipesResult:
    def __init__(self, recipes, normalized_args):
        self.recipes = recipes
        self.normalized_args = normalized_args


class Satisfaction:
    def __init__(self):
        self.__db = DB()
        self.__opt = Optimizer(self.__db)

    async def items(self, request_input, *args):
        print("calling !items with", len(args), "arguments:", ', '.join(args))

        if len(args) == 0:
            all_items = [self.__db.items()[item_var]
                         for item_var in sorted(self.__db.items().keys())]
            return ItemsResult(all_items, "")
        if len(args) == 1:
            query_parser = QueryParser(
                list(self.__db.items().keys()))
            result = await query_parser.parse_variables(request_input, args[0])
            matched_items = [self.__db.items()[item_var]
                             for item_var in sorted(result.vars)]
            return ItemsResult(matched_items, result.normalized_query)
        raise ParseException(
            "Input must an item or item regular expression")

    async def recipes(self, request_input, *args):
        print("calling !recipes with", len(args),
              "arguments:", ', '.join(args))

        if len(args) == 0:
            all_recipes = [self.__db.recipes()[recipe_var]
                           for recipe_var in sorted(self.__db.recipes().keys())]
            return RecipesResult(all_recipes, "")
        if len(args) == 1:
            query_parser = QueryParser(
                list(self.__db.recipes().keys()))
            result = await query_parser.parse_variables(request_input, args[0])
            matched_recipes = [self.__db.recipes()[recipe_var]
                               for recipe_var in sorted(result.vars)]
            return RecipesResult(matched_recipes, result.normalized_query)
        if len(args) == 2:
            if args[0] != "using" and args[0] != "for":
                raise ParseException(
                    "Input must be in the form \"!recipes\" \"for\" | \"using\" <item>")
            query_parser = QueryParser(
                list(self.__db.items().keys()), return_all_matches=False)
            result = await query_parser.parse_variables(request_input, args[1])
            matched_item_var = result.vars[0]
            if args[0] == "using":
                return RecipesResult(self.__db.recipes_for_ingredient(matched_item_var),
                                     result.normalized_query)
            if args[0] == "for":
                return RecipesResult(self.__db.recipes_for_product(matched_item_var),
                                     result.normalized_query)
        raise ParseException(
            "Input must be in the form \"!recipes\" \"for\" | \"using\" <item>")

    def buildings(self, *args):
        print("calling !buildings with", len(
            args), "arguments:", ', '.join(args))

        if len(args) == 0:
            out = []
            for building in sorted(self.__db.crafters()):
                out.append(building)
            return '\n'.join(out)
        if len(args) == 1:
            building = args[0]
            if building not in self.__db.crafters():
                return "Unknown building: " + building
            return self.__db.crafters()[building].details()

    async def min(self, request_input, *args):
        print("calling !min with", len(args), "arguments:", ', '.join(args))
        return await self.__opt.optimize(request_input, False, *args)

    async def max(self, request_input, *args):
        print("calling !max with", len(args), "arguments:", ', '.join(args))
        return await self.__opt.optimize(request_input, True, *args)
