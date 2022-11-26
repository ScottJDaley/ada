from railroad import Choice, Diagram, Optional, Sequence

entity_query = Choice(0, "<item>", "<building>")
recipe_query = Sequence("recipe", Optional("for"), "<item>")
recipes_for_query = Sequence("recipes", Choice(0, "for", "from"), Choice(0, "item", "building"))
ingredients_for_query = Sequence("ingredients")
d = Diagram(Choice(0, entity_query, recipe_query, recipes_for_query))
f = open("query_syntax.svg", "w")
d.writeSvg(f.write)
