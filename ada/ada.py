from ada.db.db import DB
from ada.help import HelpQuery, HelpResult
from ada.info import InfoQuery, InfoResult
from ada.optimization_query import OptimizationQuery
from ada.optimizer import Optimizer
from ada.processor import Processor
from ada.query import Query
from ada.query_parser import QueryParseException, QueryParser
from ada.recipe_comparer import RecipeCompareQuery, RecipeCompareResult, RecipeComparer
from ada.result import ErrorResult, Result


class Ada(Processor):
    def __init__(self) -> None:
        self.__db = DB()
        self.__parser = QueryParser(self.__db)
        self.__opt = Optimizer(self.__db)
        self.__recipe_comp = RecipeComparer(self.__db, self.__opt)

    async def do(self, raw_query: str) -> Result:
        try:
            query = self.parse(raw_query)
        except QueryParseException as parse_exception:
            return ErrorResult(str(parse_exception))
        return await self.execute(query)

    def parse(self, raw_query: str) -> Query:
        print(f"Parsing raw query: {raw_query}\n")
        query = self.__parser.parse(raw_query)
        print(f"Parsed query: {query}\n")
        return query

    async def execute(self, query: Query) -> Result:
        print("Executing query: " + str(query) + "\n")
        if isinstance(query, HelpQuery):
            return HelpResult()
        if isinstance(query, OptimizationQuery):
            return await self.__opt.optimize(query, self)
        if isinstance(query, InfoQuery):
            return InfoResult(query.vars, query.raw_query, self)
        if isinstance(query, RecipeCompareQuery):
            return RecipeCompareResult(await self.__recipe_comp.compare(query))
        return ErrorResult("Unknown query.")

    def lookup(self, var: str):
        return self.__db.lookup(var)
