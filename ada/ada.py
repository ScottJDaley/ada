from ada.db import DB
from ada.optimizer import Optimizer
from ada.query import OptimizationQuery, InfoQuery, HelpQuery
from ada.query_parser import QueryParser, QueryParseException
from ada.result import ErrorResult, InfoResult, HelpResult


class Ada:
    def __init__(self):
        self.__db = DB()
        self.__parser = QueryParser(self.__db)
        self.__opt = Optimizer(self.__db)

    async def do(self, raw_query):
        try:
            query = self.__parser.parse(raw_query)
        except QueryParseException as parse_exception:
            return ErrorResult(str(parse_exception))

        if isinstance(query, HelpQuery):
            return HelpResult()
        if isinstance(query, OptimizationQuery):
            return await self.__opt.optimize(query)
        if isinstance(query, InfoQuery):
            return InfoResult(query.vars, query.raw_query)
        return ErrorResult("Unknown query.")
