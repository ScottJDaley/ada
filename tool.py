import pulp
import json
import optimizer
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


def main():
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
            print(satisfaction.min(*args))
        elif command == "!max":
            print(satisfaction.max(*args))
        elif command == "!items":
            print(satisfaction.items(*args))
        elif command == "!recipes":
            print(satisfaction.recipes(*args))
        elif command == "!buildings":
            print(satisfaction.buildings(*args))
        else:
            print_help()


if __name__ == "__main__":
    print("Welcome to the Satisfoptimizer!")
    main()
    print("Goodbye")
