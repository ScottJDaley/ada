from ada import Ada
import asyncio


async def main():
    ada = Ada()

    while True:
        raw_query = input()
        if raw_query == "exit":
            return
        result = await ada.do(raw_query)
        if result.has_solution():
            result.generate_graph_viz('output.gv')
        print(result)


if __name__ == "__main__":
    print("Hi my name is ADA!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Goodbye")
