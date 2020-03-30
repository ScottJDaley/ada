import pulp
import json
import optimizer
import asyncio
from db import DB
from satisfaction import Satisfaction

cmds = [
    '!min',
    '!max',
    '!items',
    '!recipes',
    '!buildings',
    '!exit',
]


def print_help():
    print("Please enter a supported command:")
    print("  " + ", ".join(cmds))


async def request_input(msg):
    print(msg)
    return input()


async def main():
    satisfaction = Satisfaction()

    print_help()
    while True:
        inputs = str.split(input(), ' ')
        if len(inputs) == 0:
            continue
        command = inputs[0]
        args = inputs[1:]

        if command == "exit" or command == '!exit':
            return
        elif command == "!min":
            result = await satisfaction.min(request_input, *args)
            if result.has_solution():
                result.generate_graph_viz('output.gv')
            print(result)
        elif command == "!max":
            result = await satisfaction.max(request_input, *args)
            if result.has_solution():
                result.generate_graph_viz('output.gv')
            print(result)
        elif command == "!items":
            result = await satisfaction.items(request_input, *args)
            items = result.items
            if len(items) == 0:
                    print("Found no matching items")
            elif len(items) == 1:
                print(items[0].details())
            else:
                for item in items:
                    print(item.var())
        elif command == "!recipes":
            result = await satisfaction.recipes(request_input, *args)
            recipes = result.recipes
            if len(recipes) == 0:
                print("Found no matching recipes")''
            elif len(recipes) == 1:
                print(recipes[0].details())
            else:
                for recipe in recipes:
                    print(recipe.var())
        elif command == "!buildings":
            print(satisfaction.buildings(*args))
        else:
            print_help()


if __name__ == "__main__":
    print("Welcome to the Satisfoptimizer!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Goodbye")
