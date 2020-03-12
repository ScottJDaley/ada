import json
from item import Item

class DB:
    def __init__(self, path):
        # Parse data file
        with open(path) as f:
            data = json.load(f)

        self.__items = {}
        self.__items_from_class_names = {}
        for item_data in data["items"].values():
            item = Item(item_data)
            self.__items[item.var()] = item
            self.__items_from_class_names[item_data["className"]] = item

        # Create a dictionary from product => [recipe => product amount]
        self.__recipes_for_product = {}
        # Create a dictionary from ingredient => [recipe => ingredient amount]
        self.__recipes_for_ingredient = {}
        self.__recipes = {}
        for recipe in data["recipes"].values():
            if not recipe["inMachine"]:
                continue
            recipe_name = "recipe:" + recipe["slug"]
            self.__recipes[recipe_name] = recipe
            for ingredient in recipe["ingredients"]:
                ingredient_name = self.__items_from_class_names[ingredient["item"]]
                if ingredient_name not in self.__recipes_for_ingredient:
                    self.__recipes_for_ingredient[ingredient_name] = {}
                self.__recipes_for_ingredient[ingredient_name][recipe_name] = 60 * \
                    ingredient["amount"] / recipe["time"]
            for product in recipe["products"]:
                product_name = self.__items_from_class_names[product["item"]]
                if product_name not in self.__recipes_for_product:
                    self.__recipes_for_product[product_name] = {}
                self.__recipes_for_product[product_name][recipe_name] = 60 * \
                    product["amount"] / recipe["time"]


    def items(self):
        return self.__items

    def recipes(self):
        return self.__recipes