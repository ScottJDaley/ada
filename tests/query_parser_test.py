from ada.query_parser import QueryParser
from ada.db.db import DB

if __name__ == "__main__":
    db = DB()
    parser = QueryParser(db)

    tests_queries = [
        "produce 60 iron rods from ? iron ore",
        "produce 60 iron plate",
        "produce 60 iron plate from ? resources",
        "produce ? power from 240 crude oil",
        "produce ? power and _ plastic from 240 crude oil",
        "produce 60 iron plate from ? weighted resources",
        "produce 60 iron plate without alternate recipes",
        "produce 60 iron plate without refineries",
        "produce ? power from 60 crude oil with only fuel generators",
        "produce 60 iron plates from only iron ore",
        "produce 60 modular frames from ? resources and 30 iron rods",
        "iron rods",
        "iron.*",
        "iron rod recipe",
        "recipe iron rod",
        "iron rod recipes",
        "recipe for iron rod",
        "recipes for iron rod",
        "recipes from iron rod",
        "recipes for iron.*",
        "steel rod",
        "recipe: steel rod",
        "recipe: alternate: steel rod"
    ]

    for query in tests_queries:
        print(parser.parse(query))

    # parser.grammar().runTests("""
    #     produce 60 iron rods from ? iron ore
    #     produce 60 iron plate
    #     produce 60 iron plate from ? resources
    #     produce ? power from 240 crude oil
    #     produce ? power and _ plastic from 240 crude oil
    #     produce 60 iron plate using ? space
    #     produce 60 iron plate from ? weighted resources
    #     produce 60 iron plate without alternate recipes
    #     produce 60 iron plate with no alternate recipes
    #     produce 60 iron plate without refineries
    #     produce ? power from 60 crude oil with only fuel generators
    #     produce 60 iron plates from only iron ore
    #     produce 60 modular frames from ? resources and 30 iron rods
    # """)
