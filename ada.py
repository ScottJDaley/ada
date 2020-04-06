from db import DB
from optimizer import Optimizer
from query import OptimizationQuery, InfoQuery
from query_parser import QueryParser, QueryParseException
from result import ErrorResult, InfoResult


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

        if isinstance(query, OptimizationQuery):
            result = await self.__opt.optimize(query)
            if result.has_solution():
                result.generate_graph_viz('output.gv')
            return result
        if isinstance(query, InfoQuery):
            return InfoResult(query.vars)
        return ErrorResult("Unknown query.")
