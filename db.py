import json
from item import Item
from recipe import Recipe

class DB:
    def __init__(self, path):
        # Parse data file
        with open(path) as f:
            data = json.load(f)

        # Parse items
        self.__items = {}
        self.__item_from_class_name = {}
        for item_data in data["items"].values():
            item = Item(item_data)
            self.__items[item.var()] = item
            if item_data["className"] == "Desc_ConveyorPole_C":
                print("FOUND IT")
            self.__item_from_class_name[item_data["className"]] = item.var()

        # Parse recipes
        # Create a dictionary from product => [recipe]
        self.__recipes_for_product = {}
        # Create a dictionary from ingredient => [recipe]
        self.__recipes_for_ingredient = {}
        self.__recipes = {}
        for recipe_data in data["recipes"].values():
            if not recipe_data["inMachine"]:
                continue
            recipe = Recipe(recipe_data, self, self.__item_from_class_name)
            self.__recipes[recipe.var()] = recipe
            for ingredient in recipe_data["ingredients"]:
                ingredient_name = self.__item_from_class_name[ingredient["item"]]
                if ingredient_name == "power-shard":
                    print("Found power share")
                if ingredient_name not in self.__recipes_for_ingredient:
                    self.__recipes_for_ingredient[ingredient_name] = []
                self.__recipes_for_ingredient[ingredient_name].append(recipe)
            for product in recipe_data["products"]:
                product_name = self.__item_from_class_name[product["item"]]
                if product_name not in self.__recipes_for_product:
                    self.__recipes_for_product[product_name] = []
                self.__recipes_for_product[product_name].append(recipe)
                
        # Parse resources
        self.__resources = []
        for resource in data["resources"].values():
            self.__resources.append(self.__item_from_class_name[resource["item"]])


    def items(self):
        return self.__items

    def recipes(self):
        return self.__recipes

    def recipes_for_product(self, product):
        if product not in self.__recipes_for_product:
            return []
        return self.__recipes_for_product[product]

    def recipes_for_ingredient(self, ingredient):
        if ingredient not in self.__recipes_for_ingredient:
            return []
        return self.__recipes_for_ingredient[ingredient]

    def resources(self):
        return self.__resources