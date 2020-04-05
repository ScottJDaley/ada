from ada import Ada
import asyncio
import sys


async def main():
    ada = Ada()

    if len(sys.argv) > 1:
        print(sys.argv)
        result = await ada.do(" ".join(sys.argv[1:]))
        print(result)
        return

    while True:
        raw_query = input()
        if raw_query == "exit" or raw_query == "quit":
            return
        result = await ada.do(raw_query)
        print(result)


if __name__ == "__main__":
    print("Hi my name is ADA!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Goodbye")
