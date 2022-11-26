from .db.recipe import Recipe
from .query import Query
from .result import Result


class CompareRecipeQuery(Query):
    def __init__(self) -> None:
        self.base_recipe: Recipe | None = None
        self.include_alternates = False

    def __str__(self):
        return f"compare {self.base_recipe.var()}" \
               f"{' with alternate recipes' if self.include_alternates else ''}"


class CompareRecipeResult(Result):
    def __init__(self, query: CompareRecipeQuery):
        self.__query = query

    def query(self):
        return self.__query

    def __str__(self):
        return "TODO"
