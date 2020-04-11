import asyncio
import sys
import traceback

from ada.ada import Ada
from ada.result import OptimizationResult

DEBUG_PRINTS = False


class TracePrints(object):
    def __init__(self):
        self.stdout = sys.stdout

    def write(self, s):
        self.stdout.write("Writing %r\n" % s)
        traceback.print_stack(file=self.stdout)

    def flush(self):
        pass


if DEBUG_PRINTS:
    sys.stdout = TracePrints()


async def main():
    ada = Ada()

    if len(sys.argv) > 1:
        result = await ada.do(" ".join(sys.argv[1:]))
        print(result)
        return

    while True:
        raw_query = input()
        if raw_query == "exit" or raw_query == "quit":
            return
        result = await ada.do(raw_query)
        if isinstance(result, OptimizationResult) and result.has_solution():
            result.generate_graph_viz('output/output.gv')
        print(result)


if __name__ == "__main__":
    print("Hi my name is ADA!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Goodbye")
