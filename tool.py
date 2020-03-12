import pulp
import json
import optimizer
from db import DB
from satisfaction import Satisfaction


def print_help():
    print("Please enter a supported command ('!min', '!max', !items, '!recipes', 'exit', '!exit').")


def main():

    satisfaction = Satisfaction()
    opt = optimizer.Optimizer(DB("data.json"))

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
            print(opt.cmd_min(*args))
        elif command == "!max":
            print(opt.cmd_max(*args))
        elif command == "!items":
            print(satisfaction.items(*args))
        elif command == "!recipes":
            print(satisfaction.recipes(*args))
        else:
            print_help()


if __name__ == "__main__":
    print("Welcome to the Satisfoptimizer!")
    main()
    print("Goodbye")
