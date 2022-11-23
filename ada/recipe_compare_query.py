from .db.item import Item
from .query import Query


class RecipeCompareQuery(Query):
    def __init__(self) -> None:
        self.product_item: Item | None = None
        self.base_recipe = None
        self.related_recipes = None
        self.include_alternates = False

    def __str__(self):
        return f"compare recipes for {self.product_item.var()}" \
               f"{' with alternate recipes' if self.include_alternates else ''}"
