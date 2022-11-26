from .db.recipe import Recipe
from .query import Query
from .result import Result


class CompareRecipeQuery(Query):
    def __init__(self, recipe: Recipe, include_alternates: bool) -> None:
        self.__recipe = recipe
        self.__include_alternates = include_alternates

    def __str__(self):
        return f"compare {self.__recipe.var()}" \
               f"{' with alternate recipes' if self.__include_alternates else ''}"

    def recipe(self) -> Recipe:
        return self.__recipe

    def include_alternates(self) -> bool:
        return self.__include_alternates


class CompareRecipeResult(Result):
    def __init__(self, query: CompareRecipeQuery):
        self.__query = query

    def query(self):
        return self.__query

    def __str__(self):
        return "TODO"
