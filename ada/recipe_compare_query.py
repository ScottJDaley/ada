from .query import Query


class RecipeCompareQuery(Query):
    def __init__(self, raw_query: str) -> None:
        self.raw_query = raw_query
        self.product_item = None
        self.base_recipe = None
        self.related_recipes = None
        self.include_alternates = False

    def __str__(self):
        return self.raw_query
