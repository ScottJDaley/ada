import asyncio
import sys
import traceback

from ada.ada import Ada
from ada.optimizer import OptimizationResult

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

    async def handle_query(raw_query):
        result = await ada.query(raw_query)
        if isinstance(result, OptimizationResult) and result.has_solution():
            result.generate_graph_viz("output/output.gv")
        print(result)

    if len(sys.argv) > 1:
        await handle_query(" ".join(sys.argv[1:]))
        return

    while True:
        raw_query = input()
        if raw_query == "exit" or raw_query == "quit":
            return
        await handle_query(raw_query)


if __name__ == "__main__":
    print("Hi my name is ADA!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Goodbye")
