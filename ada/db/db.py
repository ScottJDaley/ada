# JSON data should be copied from {Install Directory}\CommunityResources\Docs\Docs.json
# into data\Docs.json

import json
import pkgutil

from .crafter import Crafter
from .entity import Entity
from .extractor import Extractor
from .item import Item
from .power_generator import PowerGenerator
from .power_recipe import PowerRecipe
from .recipe import Recipe

RESOURCE_CLASSES = [
    "FGResourceDescriptor",
]
ITEM_CLASSES = [
    "FGItemDescriptor",
    "FGEquipmentDescriptor",
    "FGItemDescriptorBiomass",
    "FGItemDescriptorNuclearFuel",
    "FGConsumableDescriptor",
    "FGBuildingDescriptor",
    "FGPoleDescriptor",
    "FGVehicleDescriptor",
    "FGAmmoTypeProjectile",
    "FGAmmoTypeInstantHit",
]
CRAFTER_CLASSES = [
    "FGBuildableManufacturer",
]
EXTRACTOR_CLASSES = [
    "FGBuildableResourceExtractor",
]
GENERATOR_CLASSES = [
    "FGBuildableGeneratorFuel",
    "FGBuildableGeneratorNuclear",
    "FGBuildableGeneratorGeoThermal",
]
RECIPE_CLASSES = [
    "FGRecipe",
]


class DB:
    def __init__(self):
        # Parse data file
        raw = pkgutil.get_data("ada.data", "Docs.json")
        if not raw:
            raise FileNotFoundError("Cannot find data file 'data/Docs.json'")
        data = json.loads(raw)

        native_classes = {}
        for native_class in data:
            native_class_name = native_class["NativeClass"].split(".")[-1][:-1]
            native_classes[native_class_name] = native_class["Classes"]

        self.__items = {}
        self.__item_var_from_class_name = {}
        self.__item_vars_from_native_class_name = {}

        # Parse resources
        for resource_class in RESOURCE_CLASSES:
            self.__item_vars_from_native_class_name[resource_class] = []
            for resource_data in native_classes[resource_class]:
                item = Item(resource_data, resource_class, is_resource=True)
                self._add_item(item)
                self.__item_var_from_class_name[item.class_name()] = item.var()
                self.__item_vars_from_native_class_name[resource_class].append(
                    item.var()
                )

        # Parse items
        for item_class in ITEM_CLASSES:

            self.__item_vars_from_native_class_name[item_class] = []
            for item_data in native_classes[item_class]:
                item = Item(item_data, item_class, is_resource=False)
                self._add_item(item)
                self.__item_var_from_class_name[item.class_name()] = item.var()
                self.__item_vars_from_native_class_name[item_class].append(
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

        # Parse extractors
        self.__extractors = {}
        self.__extractors_var_from_class_name = {}
        for extractor_class in EXTRACTOR_CLASSES:
            for building_data in native_classes[extractor_class]:
                extractor = Extractor(building_data)
                self.__extractors[extractor.var()] = extractor
                self.__extractors_var_from_class_name[
                    extractor.class_name()
                ] = extractor.var()

        # Parse generators
        self.__generators = {}
        for generator_class in GENERATOR_CLASSES:
            for generator_data in native_classes[generator_class]:
                generator = PowerGenerator(generator_data, self.__items.values())
                self.__generators[generator.var()] = generator

        # Parse recipes
        # Create a dictionary from product => [recipe]
        self.__recipes_for_product = {}
        # Create a dictionary from ingredient => [recipe]
        self.__recipes_for_ingredient = {}
        self.__recipes = {}
        for recipe_class in RECIPE_CLASSES:
            for recipe_data in native_classes[recipe_class]:
                recipe = Recipe(
                    recipe_data, self.__items.values(), self.__crafters.values()
                )
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
                # print(f"Found power recipe var {power_recipe.var()}")
                self.__power_recipes[power_recipe.var()] = power_recipe
                self.__power_recipes_by_fuel[fuel_item.var()] = power_recipe

        self.__all_entities = self.__items | self.__crafters | self.__extractors | self.__generators | self.__recipes \
                              | self.__power_recipes

    def _add_item(self, item: Item):
        if item.var() in self.__items:
            existing = self.__items[item.var()]
            print(f"Found duplicate item var {item.var()}, old {existing.class_name()}, new {item.class_name()}")
        self.__items[item.var()] = item

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

    def recipes_for_product(self, product) -> list[Recipe]:
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

    def crafters(self):
        return self.__crafters

    def crafter_from_class_name(self, class_name):
        if class_name not in self.__crafter_var_from_class_name:
            return None
        return self.crafters()[self.__crafter_var_from_class_name[class_name]]

    def extractors(self):
        return self.__extractors

    def extractor_from_class_name(self, class_name):
        if class_name not in self.__extractors_var_from_class_name:
            return None
        return self.extractors()[self.__extractors_var_from_class_name[class_name]]

    def generators(self):
        return self.__generators

    def lookup(self, var: str) -> Entity | None:
        if var in self.__all_entities:
            return self.__all_entities[var]
        return None
