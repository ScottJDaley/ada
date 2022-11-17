from typing import Union

from ada.db.db import DB
from ada.help import HelpQuery, HelpResult
from ada.info import InfoQuery, InfoResult
from ada.optimizer import OptimizationQuery, Optimizer
from ada.processor import Processor
from ada.query_parser import QueryParseException, QueryParser
from ada.recipe_comparer import RecipeCompareQuery, RecipeComparer, RecipeCompareResult
from ada.result import Result, ErrorResult


class Ada(Processor):
    def __init__(self) -> None:
        self.__db = DB()
        self.__parser = QueryParser(self.__db)
        self.__opt = Optimizer(self.__db)
        self.__recipe_comp = RecipeComparer(self.__db, self.__opt)

    async def do(
        self, raw_query: str
    ) -> Result:
        print("Query: " + raw_query + "\n")
        try:
            query = self.__parser.parse(raw_query)
        except QueryParseException as parse_exception:
            return ErrorResult(str(parse_exception))

        if isinstance(query, HelpQuery):
            return HelpResult()
        if isinstance(query, OptimizationQuery):
            return await self.__opt.optimize(query)
        if isinstance(query, InfoQuery):
            return InfoResult(query.vars, query.raw_query, self)
        if isinstance(query, RecipeCompareQuery):
            return RecipeCompareResult(await self.__recipe_comp.compare(query))
        return ErrorResult("Unknown query.")

    def lookup(self, var: str):
        return self.__db.lookup(var)

