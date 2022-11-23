from typing import Callable, Generic, TypeVar

from .query import Query


class MaximizeValue:
    def __str__(self):
        return "?"


class AnyValue:
    def __str__(self):
        return "_"


class AmountValue:
    def __init__(self, value: float):
        self.value = value

    def __str__(self, ):
        return str(self.value)


class Input:
    def __init__(self, var: str, value: AmountValue | MaximizeValue | AnyValue):
        self.var = var
        self.value = value

    def __str__(self):
        return f"{self.value} {self.var}"


class Output:
    def __init__(self, var: str, value: AmountValue | MaximizeValue | AnyValue):
        self.var = var
        self.value = value

    def __str__(self):
        return f"{self.value} {self.var}"


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
        self.__inputs: dict[str, Category[Input]] = {"resource": Category("item", False)}
        self.__outputs: dict[str, Category[Output]] = {"item": Category("item", False)}
        self.__includes: dict[str, Category[Include]] = {
            "crafter": Category("crafter", True),
            "generator": Category("generator", True),
            "recipe": Category("recipe", True),
            "power-recipe": Category("power-recipe", True),
        }
        self.__excludes: dict[str, Category[Exclude]] = {}
        self.__objective: Input | Output | None = None

    def objective(self) -> Input | Output | None:
        return self.__objective

    def has_objective(self) -> bool:
        return self.__objective is not None

    def add_output(self, var: str, value: AmountValue | MaximizeValue | AnyValue, strict: bool):
        print(f"Adding output, var={var}, amount={value}, strict={strict}")
        output = Output(var, value)
        if isinstance(value, MaximizeValue):
            self.__objective = output
        _add_element(self.__outputs, var, output, strict)

    def remove_output(self, var: str):
        print(f"Remove output, var={var}")
        _remove_element(self.__outputs, var)

    def add_input(self, var: str, value: AmountValue | MaximizeValue | AnyValue, strict: bool):
        print(f"Adding input, var={var}, amount={value}, strict={strict}")
        input = Input(var, value)
        if isinstance(value, MaximizeValue):
            self.__objective = input
        _add_element(self.__inputs, var, input, strict)

    def remove_input(self, var: str):
        print(f"Remove input, var={var}")
        _remove_element(self.__inputs, var)

    def add_include(self, var: str):
        print(f"Adding include, var={var}")
        _add_element(self.__includes, var, Include(var), False)

    def remove_include(self, var: str):
        print(f"Remove include, var={var}")
        _remove_element(self.__includes, var)

    def add_exclude(self, var: str):
        print(f"Adding exclude, var={var}")
        _add_element(self.__excludes, var, Exclude(var), False)

    def inputs(self):
        return self.__inputs

    def outputs(self):
        return self.__outputs

    def includes(self):
        return self.__includes

    def excludes(self):
        return self.__excludes

    def strict_inputs(self):
        return self.__inputs["resource"].strict

    def strict_outputs(self):
        return self.__outputs["item"].strict

    def set_strict_inputs(self, value: bool):
        self.__inputs["resource"].strict = value

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

        # if isinstance(self.__objective, Output):
        #     outputs.append(f"? {self.__objective.var}")
        # elif isinstance(self.__objective, Input):
        #     inputs.append(f"? {self.__objective.var}")

        for category in self.__outputs.values():
            values = category.elements.values()
            if len(values) == 0:
                continue
            outputs.append(f"{'only ' if category.strict else ''}{' '.join([str(value) for value in values])}")

        for category in self.__inputs.values():
            values = category.elements.values()
            if len(values) == 0:
                continue
            inputs.append(f"{'only ' if category.strict else ''}{' and '.join([str(value) for value in values])}")

        for category in self.__includes.values():
            values = category.elements.values()
            if len(values) == 0:
                continue
            includes.append(f"{'only ' if category.strict else ''}{' '.join([str(value) for value in values])}")

        for category in self.__excludes.values():
            values = category.elements.values()
            if len(values) == 0:
                continue
            excludes.append(f"{'only ' if category.strict else ''}{' '.join([str(value) for value in values])}")

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
        query_vars = []
        if self.has_objective():
            query_vars.append(self.__objective.var)
        for category in self.__outputs.values():
            query_vars.extend(category.elements.keys())
        for category in self.__inputs.values():
            query_vars.extend(category.elements.keys())
        for category in self.__includes.values():
            query_vars.extend(category.elements.keys())
        for category in self.__excludes.values():
            query_vars.extend(category.elements.keys())
        return query_vars
