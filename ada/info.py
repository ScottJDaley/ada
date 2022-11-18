import math
from typing import List

import discord

from ada.breadcrumbs import Breadcrumbs
from ada.db.entity import Entity
from ada.processor import Processor
from ada.result import Result, ResultMessage
from ada.views.multi_entity import MultiEntityView
from ada.views.with_previous import WithPreviousView


class InfoQuery:
    def __init__(self, raw_query: str) -> None:
        self.raw_query = raw_query
        self.vars = []

    def __str__(self):
        if len(self.vars) == 1:
            return self.vars[0].details()
        return "\n".join([var.human_readable_name() for var in self.vars])


class InfoResult(Result):
    num_on_page = 9

    def __init__(self, vars_: List[Entity], raw_query: str, processor: Processor) -> None:
        self.__entities = sorted(vars_, key=lambda var_: var_.human_readable_name())
        self.__raw_query = raw_query
        self.__processor = processor

    def __str__(self):
        if len(self.__entities) == 1:
            return self.__entities[0].details()
        var_names = [var.human_readable_name() for var in self.__entities]
        var_names.sort()
        return "\n".join(var_names)

    def _num_pages(self):
        return math.ceil(len(self.__entities) / InfoResult.num_on_page)

    def _footer(self, page):
        return "Page " + str(page) + " of " + str(self._num_pages())

    def _get_var_on_page(self, page, index):
        var_index = (page - 1) * InfoResult.num_on_page + index
        return self.__entities[var_index]

    def _get_info_page(self, breadcrumbs: Breadcrumbs) -> ResultMessage:
        message = ResultMessage()
        message.embed = None
        message.file = None
        message.content = str(breadcrumbs)
        message.view = MultiEntityView(self.__entities, breadcrumbs.current_page().custom_ids()[0], self.__processor)
        if breadcrumbs.has_prev_page():
            message.view = WithPreviousView(message.view, self.__processor)
        return message

    def message(self, breadcrumbs: Breadcrumbs) -> ResultMessage:
        if len(self.__entities) == 0:
            message = ResultMessage()
            message.embed = discord.Embed(title="No matches found")
            message.content = str(breadcrumbs)
            return message
        if len(self.__entities) > 1:
            return self._get_info_page(breadcrumbs)

        breadcrumbs.current_page().replace_query(self.__entities[0].var())
        message = ResultMessage()
        message.embed = self.__entities[0].embed()
        message.file = None
        message.view = self.__entities[0].view(self.__processor)
        if breadcrumbs.has_prev_page():
            message.view = WithPreviousView(message.view, self.__processor)
        message.content = str(breadcrumbs)
        return message
