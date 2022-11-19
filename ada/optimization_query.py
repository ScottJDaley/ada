from typing import TypeVar, Generic, Callable, Any

from ada.query import Query



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


def _add_element(dictionary: dict[str, Category], category: str, var: str, element: T, strict: bool):
    if category not in dictionary:
        dictionary[category] = Category(category, strict)
    dictionary[category].elements[var] = element
    dictionary[category].strict |= strict


class OptimizationQuery(Query):
    def __init__(self, raw_query: str) -> None:
        self.raw_query = raw_query

        self.inputs: dict[str, Category[Input]] = {"item": Category("item", False)}
        self.outputs: dict[str, Category[Output]] = {"item": Category("item", False)}
        self.includes: dict[str, Category[Include]] = {"crafter": Category("crafter", False),
                                                       "generator": Category("generator", False),
                                                       "recipe": Category("recipe", False),
                                                       "power-recipe": Category("power-recipe", False),}
        self.excludes: dict[str, Category[Exclude]] = {}
        self.objective: Objective | None = None

    def add_output(self, category: str, var: str, amount: int | None, strict: bool):
        print(f"Adding output, cat={category}, var={var}, amount={amount}, strict={strict}")
        _add_element(self.outputs, category, var, Output(var, amount), strict)

    def add_input(self, category: str, var: str, amount: int | None, strict: bool):
        print(f"Adding input, cat={category}, var={var}, amount={amount}, strict={strict}")
        _add_element(self.inputs, category, var, Input(var, amount), strict)

    def add_include(self, category: str, var: str):
        print(f"Adding include, cat={category}, var={var}")
        _add_element(self.includes, category, var, Include(var), True)

    def add_exclude(self, category: str, var: str):
        print(f"Adding exclude, cat={category}, var={var}")
        _add_element(self.excludes, category, var, Exclude(var), False)

    def maximize_objective(self) -> bool:
        return self.objective.maximize

    def objective_coefficients(self) -> dict[str, int]:
        return {self.objective.var: self.objective.coefficient}

    def eq_constraints(self) -> dict[str, float]:
        result = {}

        def process_output(var: str, output: Output):
            if output.has_amount():
                result[var] = output.amount

        def process_exclude(var: str, exclude: Exclude):
            result[var] = 0

        for_all_elements(self.outputs, process_output)
        for_all_elements(self.excludes, process_exclude)

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

        for_all_elements(self.outputs, process_output)
        for_all_elements(self.inputs, process_input)
        for_all_elements(self.includes, process_include)

        return result

    def le_constraints(self) -> dict[str, float]:
        result = {}

        def process_input(var: str, input: Input):
            if not input.has_amount():
                result[var] = 0

        for_all_elements(self.inputs, process_input)

        return result

    def strict_inputs(self):
        return self.inputs["item"].strict

    def strict_outputs(self):
        return self.outputs["item"].strict

    def strict_crafters(self):
        return self.includes["crafter"].strict

    def strict_generators(self):
        return self.includes["generator"].strict

    def strict_recipes(self):
        return self.includes["recipe"].strict

    def strict_power_recipes(self):
        return self.includes["power-recipe"].strict

    def has_power_output(self):
        return "power" in self.outputs

    def __str__(self) -> str:

        outputs = []
        inputs = []
        includes = []
        excludes = []

        if self.objective.maximize:
            outputs.append(f"? {self.objective.var}")
        else:
            inputs.append(f"? {self.objective.var}")

        for category in self.outputs.values():
            for output in category.elements.values():
                outputs.append(f"{output.amount} {output.var}")

        for category in self.inputs.values():
            for inputs in category.elements.values():
                inputs.append(f"{inputs.amount} {inputs.var}")

        for category in self.includes.values():
            for include in category.elements.values():
                includes.append(f"{include.var}")

        for category in self.excludes.values():
            for exclude in category.elements.values():
                excludes.append(f"{exclude.var}")

        output_str = f"produce {'and'.join(outputs)}"
        input_str = f"from {'and'.join(inputs)}" if len(inputs) > 0 else ""
        include_str = f"using {'and'.join(includes)}" if len(includes) > 0 else ""
        exclude_str = f"without {'or'.join(excludes)}" if len(excludes) > 0 else ""

        return " ".join([output_str, input_str, include_str, exclude_str])

    def print(self):
        print(self)

    def query_vars(self) -> list[str]:
        query_vars = [self.objective.var]
        for category in self.outputs.values():
            query_vars.extend(category.elements.keys())
        for category in self.inputs.values():
            query_vars.extend(category.elements.keys())
        for category in self.includes.values():
            query_vars.extend(category.elements.keys())
        for category in self.excludes.values():
            query_vars.extend(category.elements.keys())
        return query_vars
