from typing import Dict, List, Tuple

from ada.db.item import Item
from discord import Embed


def parse_list(raw: str) -> List[str]:
    if raw.startswith("(("):
        return raw[2:-2].split("),(")
    return raw[1:-1].split(",")


def parse_recipe_item(raw: str) -> Tuple[str, int]:
    components = raw.split(",")
    component_map = {}
    for component in components:
        key_value = component.split("=")
        component_map[key_value[0]] = key_value[1]
    class_name = component_map["ItemClass"].split(".")[1][:-2]
    return class_name, int(component_map["Amount"])


class BuildableRecipeItem:
    def __init__(self, item: Item, amount: int) -> None:
        self.__item = item
        self.__amount = amount

    def item(self) -> Item:
        return self.__item

    def amount(self) -> int:
        return self.__amount

    def human_readable_name(self):
        return f"{self.item().human_readable_name()}: {self.amount()}"


class BuildableRecipe:
    def __init__(self, data: Dict[str, str], buildables) -> None:
        self.__data = data

        # item var => recipe item
        self.__ingredients = {}
        self.__product = None
        for ingredient in parse_list(data["mIngredients"]):
            class_name, amount = parse_recipe_item(ingredient)
            for buildable in buildables:
                if buildable.class_name() != class_name:
                    continue
                self.__ingredients[buildable.var()] = BuildableRecipeItem(
                    buildable, amount
                )
        for product in parse_list(data["mProduct"]):
            class_name, amount = parse_recipe_item(product)
            for buildable in buildables:
                buildable_class_name_suffix = (
                    buildable.class_name().removeprefix("Build_").removeprefix("Desc_")
                )
                product_class_name_suffix = class_name.removeprefix(
                    "Desc_"
                ).removeprefix("Build_")
                if buildable_class_name_suffix != product_class_name_suffix:
                    # if buildable.class_name() != class_name:
                    # if "Ladder" in class_name and "Ladder" in buildable.class_name():
                    #     print(
                    #         f"What the fuck {buildable.class_name()} vs. {class_name}"
                    #     )
                    # if "Ladder" in class_name:
                    #     print(f"considering {buildable.class_name()}")
                    continue
                self.__product = buildable
                break
        # if self.__product:
        #     print(f"Product var {self.__product.var()}")
        # else:
        #     # print(f"Could not find product class {class_name}")
        #     print(f"Could not find {product_class_name_suffix}")
        if not self.__product:
            print(f"Could not find product class '{class_name}'")

    def slug(self) -> str:
        return self.__data["mDisplayName"].lower().replace(" ", "-").replace(":", "")

    def var(self) -> str:
        return "buildable-recipe:" + self.slug()

    def human_readable_name(self) -> str:
        return "Recipe: " + self.__data["mDisplayName"]

    def details(self):
        out = [
            self.human_readable_name(),
            "  var: " + self.var(),
            "  ingredients:"
        ]
        for ingredient in self.__ingredients.values():
            out.append("    " + ingredient.human_readable_name())
        out.append("")
        return "\n".join(out)

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        ingredients = "\n".join(
            [ing.human_readable_name() for ing in self.ingredients().values()]
        )
        embed.add_field(name="Ingredients", value=ingredients, inline=True)
        return embed

    def ingredients(self) -> Dict[str, BuildableRecipeItem]:
        return self.__ingredients

    def product(self) -> Item:
        return self.__product

    def ingredient(self, var: str) -> BuildableRecipeItem:
        return self.__ingredients[var]
