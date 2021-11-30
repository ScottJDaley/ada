# JSON data should be copied from {Install Directory}\CommunityResources\Docs\Docs.json
# into data\Docs.json

import json
from ada.crafter import Crafter
from ada.generator import Generator
from ada.item import Item
from ada.recipe import Recipe
from ada.power_recipe import PowerRecipe

RESOURCE_CLASSES = [
    "Class'/Script/FactoryGame.FGResourceDescriptor'",
]
ITEM_CLASSES = [
    "Class'/Script/FactoryGame.FGItemDescriptor'",
    "Class'/Script/FactoryGame.FGEquipmentDescriptor'",
    "Class'/Script/FactoryGame.FGItemDescriptorBiomass'",
    "Class'/Script/FactoryGame.FGItemDescriptorNuclearFuel'",
    "Class'/Script/FactoryGame.FGConsumableDescriptor'",
    "Class'/Script/FactoryGame.FGItemDescAmmoTypeColorCartridge'",
    "Class'/Script/FactoryGame.FGItemDescAmmoTypeProjectile'",
    "Class'/Script/FactoryGame.FGItemDescAmmoTypeInstantHit'",
]
CRAFTER_CLASSES = [
    "Class'/Script/FactoryGame.FGBuildableManufacturer'",
]
GENERATOR_CLASSES = [
    "Class'/Script/FactoryGame.FGBuildableGeneratorFuel'",
    "Class'/Script/FactoryGame.FGBuildableGeneratorNuclear'",
    "Class'/Script/FactoryGame.FGBuildableGeneratorGeoThermal'",
]
RECIPE_CLASSES = [
    "Class'/Script/FactoryGame.FGRecipe'",
]


class DB:
    def __init__(self):
        # Parse data file
        with open("data/Docs.json", encoding="utf8") as f:
            data = json.load(f)

        native_classes = {}
        for native_class in data:
            native_classes[native_class["NativeClass"]] = native_class["Classes"]

        self.__items = {}
        self.__item_var_from_class_name = {}
        self.__item_vars_from_native_class_name = {}

        # Parse resources
        for resource_class in RESOURCE_CLASSES:
            resource_class_short = resource_class.split(".")[1][:-1]
            self.__item_vars_from_native_class_name[resource_class_short] = []
            for resource_data in native_classes[resource_class]:
                item = Item(resource_data, is_resource=True)
                self.__items[item.var()] = item
                self.__item_var_from_class_name[item.class_name()] = item.var()
                self.__item_vars_from_native_class_name[resource_class_short].append(
                    item.var()
                )
        # Parse items
        for item_class in ITEM_CLASSES:
            item_class_short = item_class.split(".")[1][:-1]
            self.__item_vars_from_native_class_name[item_class_short] = []
            for item_data in native_classes[item_class]:
                item = Item(item_data, is_resource=False)
                self.__items[item.var()] = item
                self.__item_var_from_class_name[item.class_name()] = item.var()
                self.__item_vars_from_native_class_name[item_class_short].append(
                    item.var()
                )

        # Parse crafters
        self.__crafters = {}
        self.__crafter_var_from_class_name = {}
        for crafter_class in CRAFTER_CLASSES:
            for building_data in native_classes[crafter_class]:
                crafter = Crafter(building_data)
                self.__crafters[crafter.var()] = crafter
                self.__crafter_var_from_class_name[crafter.class_name()] = crafter.var()

        # Parse generators
        self.__generators = {}
        for generator_class in GENERATOR_CLASSES:
            for generator_data in native_classes[generator_class]:
                generator = Generator(generator_data, self)
                self.__generators[generator.var()] = generator

        # Parse recipes
        # Create a dictionary from product => [recipe]
        self.__recipes_for_product = {}
        # Create a dictionary from ingredient => [recipe]
        self.__recipes_for_ingredient = {}
        self.__recipes = {}
        for recipe_class in RECIPE_CLASSES:
            for recipe_data in native_classes[recipe_class]:
                recipe = Recipe(recipe_data, self)
                if not recipe.is_craftable_in_building():
                    continue
                self.__recipes[recipe.var()] = recipe
                for ingredient in recipe.ingredients().keys():
                    if ingredient not in self.__recipes_for_ingredient:
                        self.__recipes_for_ingredient[ingredient] = []
                    self.__recipes_for_ingredient[ingredient].append(recipe)
                for product in recipe.products().keys():
                    if product not in self.__recipes_for_product:
                        self.__recipes_for_product[product] = []
                    self.__recipes_for_product[product].append(recipe)

        # Create power recipes
        self.__power_recipes = {}
        self.__power_recipes_by_fuel = {}
        for generator in self.__generators.values():
            for fuel_item in generator.fuel_items():
                if fuel_item.energy_value() <= 0:
                    continue
                power_recipe = PowerRecipe(fuel_item, generator)
                self.__power_recipes[power_recipe.var()] = power_recipe
                self.__power_recipes_by_fuel[fuel_item.var()] = power_recipe

    def items(self):
        return self.__items

    def item_from_class_name(self, class_name):
        return self.items()[self.__item_var_from_class_name[class_name]]

    def items_from_native_class_name(self, class_name):
        if class_name not in self.__item_vars_from_native_class_name:
            return None
        return [
            self.__items[item_var]
            for item_var in self.__item_vars_from_native_class_name[class_name]
        ]

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

    def power_recipes(self):
        return self.__power_recipes

    def power_recipes_by_fuel(self):
        return self.__power_recipes_by_fuel

    def resources(self):
        return self.__resources

    def crafters(self):
        return self.__crafters

    def crafter_from_class_name(self, class_name):
        if class_name not in self.__crafter_var_from_class_name:
            return None
        return self.crafters()[self.__crafter_var_from_class_name[class_name]]

    def generators(self):
        return self.__generators
