from railroad import Choice, Diagram, Group, OneOrMore, Optional, Sequence, Stack

queries = {
    "entity_query": Choice(0, "<item>", "<recipe>", "<building>"),
    "recipe_query": Sequence("recipe", Optional("for"), "<item>"),
    "recipes_query": Sequence("recipes", Choice(0, "for", "from"), Choice(0, "item", "building")),
    "compare_recipe_query": Sequence("compare", "<recipe>"),
    "compare_recipes_for_query": Sequence("compare", "recipes", "for", "<item>"),
    "ingredients_for_query": Sequence("ingredients", "for", "<recipe>"),
    "products_for_query": Sequence("products", "for", "<recipe>"),
    "optimization_query": Stack(
        Group(
            Sequence(
                Choice(0, "produce", "make", "create", "output"),
                OneOrMore(
                    Sequence(
                        Optional("only"),
                        Optional(Choice(0, "?", "_", "no", "<amount>")),
                        Choice(0, "<item>", "power")
                    ), "and"
                )
            ), "Outputs"
        ),
        Group(
            Optional(
                Sequence(
                    Choice(0, "from", "using", "with", "input"),
                    OneOrMore(
                        Sequence(
                            Choice(
                                0,
                                Sequence(
                                    Optional("only"),
                                    Optional(Choice(0, "?", "_", "no", "<amount>")),
                                    Choice(0, "<item>", "<recipe>", "<building>", "power")
                                ),
                                "alternate-recipes",
                                "weighted-resources",
                                "unweighted-resources",
                            )
                        ), "and"
                    )
                )
            ), "Inputs"
        ),
        Group(
            Optional(
                Sequence(
                    Choice(0, "without", "excluding"),
                    OneOrMore(Choice(0, "<item>", "<recipe>", "<building>", "alternate-recipes"))
                )
            ), "Excludes"
        )
    )
}

for name, query in queries.items():
    d = Diagram(Sequence("/ada", query))
    f = open(f"{name}.svg", "w")
    d.writeSvg(f.write)
