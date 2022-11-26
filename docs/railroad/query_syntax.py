from railroad import Choice, Diagram, Group, OneOrMore, Optional, Sequence, Stack

# Run this file to generate the svg images that are used in the README.

queries = {
    "info_query": Choice(
        0,
        Group(Choice(0, "<item>", "<recipe>", "<building>"), "Entity Lookup"),
        Group(
            Sequence(
                Choice(
                    0,
                    Sequence("recipe", Optional("for")),
                    Sequence("recipes", Choice(0, "for", "from"))
                ),
                Choice(0, "<item>", "<building>")
            ),
            "Recipe Lookup"
        ),
        Group(Sequence("compare", Choice(0, Sequence("recipes", "for", "<item>"), "<recipe>")), "Recipe Comparison"),
        Group(
            Choice(
                0,
                Sequence("ingredients", "for", "<recipe>"),
                Sequence("products", "for", "<recipe>")
            ),
            "Recipe Details"
        )
    ),
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
