from typing import Callable, Generic, TypeVar

from .query import Query


class Input:
    def __init__(self, var: str, amount: int | None):
        self.var = var
        self.amount = amount

    def __str__(self):
        if self.has_amount():
            return f"{self.amount} {self.var}"
        return self.var

    def has_amount(self):
        return self.amount is not None


class Output:
    def __init__(self, var: str, amount: int | None):
        self.var = var
        self.amount = amount

    def __str__(self):
        if self.has_amount():
            return f"{self.amount} {self.var}"
        return self.var

    def has_amount(self):
        return self.amount is not None


class Include:
    def __init__(self, var: str):
        self.var = var

    def __str__(self):
        return self.var


class Exclude:
    def __init__(self, var: str):
        self.var = var

    def __str__(self):
        return self.var


# TODO: Remove maximize and coefficient after testing that non-negated inputs work as expected with max.
class Objective:
    def __init__(self, var: str, maximize: bool, coefficient: int):
        self.var = var
        self.maximize = maximize
        self.coefficient = coefficient


T = TypeVar("T")


class Category(Generic[T]):
    def __init__(self, name: str, strict: bool):
        self.name = name
        self.strict = strict
        self.elements: dict[str, T] = {}


def for_all_elements(section: dict[str, Category[T]], func: Callable[[str, T], None]):
    for name, category in section.items():
        for var, element in category.elements.items():
            func(var, element)


def _add_element(dictionary: dict[str, Category], var: str, element: T, strict: bool):
    category = var.split(":")[0]
    if category not in dictionary:
        dictionary[category] = Category(category, strict)
    dictionary[category].elements[var] = element
    dictionary[category].strict |= strict


def _remove_element(dictionary: dict[str, Category], var: str):
    print(f"Attempting to remove var {var}")
    category = var.split(":")[0]
    if category not in dictionary:
        print(f"Can't find category {category} to remove")
        return
    if var not in dictionary[category].elements:
        print(f"Can't find var {var} to remove")
    dictionary[category].elements.pop(var)


class OptimizationQuery(Query):
    def __init__(self) -> None:
        self.__inputs: dict[str, Category[Input]] = {"item": Category("item", False)}
        self.__outputs: dict[str, Category[Output]] = {"item": Category("item", False)}
        self.__includes: dict[str, Category[Include]] = {
            "crafter": Category("crafter", True),
            "generator": Category("generator", True),
            "recipe": Category("recipe", True),
            "power-recipe": Category("power-recipe", True),
        }
        self.__excludes: dict[str, Category[Exclude]] = {}
        self.__objective: Objective | None = None

    def has_objective(self) -> bool:
        return self.__objective is not None

    def add_objective(self, objective: Objective) -> None:
        self.__objective = objective

    def add_output(self, var: str, amount: int | None, strict: bool):
        print(f"Adding output, var={var}, amount={amount}, strict={strict}")
        _add_element(self.__outputs, var, Output(var, amount), strict)

    def add_input(self, var: str, amount: int | None, strict: bool):
        print(f"Adding input, var={var}, amount={amount}, strict={strict}")
        _add_element(self.__inputs, var, Input(var, amount), strict)

    def add_include(self, var: str):
        print(f"Adding include, var={var}")
        _add_element(self.__includes, var, Include(var), False)

    def remove_include(self, var: str):
        print(f"Remove include, var={var}")
        _remove_element(self.__includes, var)

    def add_exclude(self, var: str):
        print(f"Adding exclude, var={var}")
        _add_element(self.__excludes, var, Exclude(var), False)

    def maximize_objective(self) -> bool:
        return self.__objective.maximize

    def objective_coefficients(self) -> dict[str, int]:
        return {self.__objective.var: self.__objective.coefficient}

    def eq_constraints(self) -> dict[str, float]:
        result = {}

        def process_output(var: str, output: Output):
            if output.has_amount():
                result[var] = output.amount

        def process_exclude(var: str, exclude: Exclude):
            result[var] = 0

        for_all_elements(self.__outputs, process_output)
        for_all_elements(self.__excludes, process_exclude)

        return result

    def ge_constraints(self) -> dict[str, float]:
        result = {}

        def process_output(var: str, output: Output):
            if not output.has_amount():
                result[var] = 0

        def process_input(var: str, input: Input):
            if input.has_amount():
                result[var] = -input.amount

        def process_include(var: str, include: Include):
            result[var] = 0

        for_all_elements(self.__outputs, process_output)
        for_all_elements(self.__inputs, process_input)
        for_all_elements(self.__includes, process_include)

        return result

    def le_constraints(self) -> dict[str, float]:
        result = {}

        def process_input(var: str, input: Input):
            if not input.has_amount():
                result[var] = 0

        for_all_elements(self.__inputs, process_input)

        return result

    def strict_inputs(self):
        return self.__inputs["item"].strict and len(self.__inputs["item"].elements) > 0

    def strict_outputs(self):
        return self.__outputs["item"].strict

    def set_strict_outputs(self, value: bool):
        self.__outputs["item"].strict = value

    def strict_crafters(self):
        return self.__includes["crafter"].strict and len(self.__includes["crafter"].elements) > 0

    def strict_generators(self):
        return self.__includes["generator"].strict and len(self.__includes["generator"].elements) > 0

    def strict_recipes(self):
        return self.__includes["recipe"].strict and len(self.__includes["recipe"].elements) > 0

    def strict_power_recipes(self):
        return self.__includes["power-recipe"].strict and len(self.__includes["power-recipe"].elements) > 0

    def has_power_output(self):
        return "power" in self.__outputs

    def __str__(self) -> str:

        outputs = []
        inputs = []
        includes = []
        excludes = []

        if self.__objective.maximize:
            outputs.append(f"? {self.__objective.var}")
        else:
            inputs.append(f"? {self.__objective.var}")

        for category in self.__outputs.values():
            for output in category.elements.values():
                outputs.append(f"{'only ' if category.strict else ''}{output.amount} {output.var}")

        for category in self.__inputs.values():
            for input in category.elements.values():
                inputs.append(f"{'only ' if category.strict else ''}{input.amount} {input.var}")

        for category in self.__includes.values():
            for include in category.elements.values():
                includes.append(f"{'only ' if category.strict else ''}{include.var}")

        for category in self.__excludes.values():
            for exclude in category.elements.values():
                excludes.append(f"{'only ' if category.strict else ''}{exclude.var}")

        parts = [f"produce {' and '.join(outputs)}"]
        if len(inputs) > 0:
            parts.append(f"from {' and '.join(inputs)}")
        if len(includes) > 0:
            parts.append(f"using {' and '.join(includes)}")
        if len(excludes) > 0:
            parts.append(f"without {' or '.join(excludes)}")

        return " ".join(parts)

    def print(self):
        print(self)

    def query_vars(self) -> list[str]:
        query_vars = [self.__objective.var]
        for category in self.__outputs.values():
            query_vars.extend(category.elements.keys())
        for category in self.__inputs.values():
            query_vars.extend(category.elements.keys())
        for category in self.__includes.values():
            query_vars.extend(category.elements.keys())
        for category in self.__excludes.values():
            query_vars.extend(category.elements.keys())
        return query_vars
