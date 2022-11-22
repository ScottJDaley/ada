from .db.crafter import Crafter
from .db.item import Item
from .db.power_generator import PowerGenerator
from .db.recipe import Recipe


class OptimizationResultData:
    def __init__(
            self,
            *,
            inputs: dict[str, tuple[Item, float]],
            outputs: dict[str, tuple[Item, float]],
            recipes: dict[str, tuple[Recipe, float]],
            crafters: dict[str, tuple[Crafter, float]],
            generators: dict[str, tuple[PowerGenerator, float]],
            net_power: float
    ) -> None:
        self.__inputs = inputs
        self.__outputs = outputs
        self.__recipes = recipes
        self.__crafters = crafters
        self.__generators = generators
        self.__net_power = net_power

    def inputs(self) -> dict[str, tuple[Item, float]]:
        return self.__inputs

    def outputs(self) -> dict[str, tuple[Item, float]]:
        return self.__outputs

    def recipes(self) -> dict[str, tuple[Recipe, float]]:
        return self.__recipes

    def crafters(self) -> dict[str, tuple[Crafter, float]]:
        return self.__crafters

    def generators(self) -> dict[str, tuple[PowerGenerator, float]]:
        return self.__generators

    def net_power(self) -> float:
        return self.__net_power
