from db import DB
from optimizer import Optimizer
from query_parser import QueryParser, QueryParseException
from result import ErrorResult


class Ada:
    def __init__(self):
        self.__db = DB()
        self.__parser = QueryParser(self.__db)
        self.__opt = Optimizer(self.__db)

    async def do(self, raw_query):
        print("calling do() with query:", raw_query)
        try:
            query = self.__parser.parse(raw_query)
        except QueryParseException as e:
            print(e)
            return ErrorResult(e.msg)

        return await self.__opt.optimize(query)
