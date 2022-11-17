import math
from typing import List

import discord
from discord.embeds import Embed

import ada.emoji
from ada.breadcrumbs import Breadcrumbs
from ada.db.entity import Entity
from ada.processor import Processor
from ada.result import Result, ResultMessage
from ada.views.multi_entity import MultiEntityView


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
        self.__add_reaction_selectors = False
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

    def _get_info_page(self, breadcrumbs):
        # var_names = [var.human_readable_name() for var in self.__entities]
        # start_index = (breadcrumbs.page() - 1) * InfoResult.num_on_page
        # last_index = start_index + InfoResult.num_on_page

        # vars_on_page = var_names[start_index:last_index]

        # out = []
        message = ResultMessage()
        # for i, var_ in enumerate(vars_on_page):
        #     prefix = ""
        #     if self.__add_reaction_selectors:
        #         prefix = ada.emoji.NUM_EMOJI[i + 1]
        #         message.reactions.append(prefix)
        #     out.append("- " + prefix + var_)
        # if not self.__add_reaction_selectors:
        #     message.reactions = []
        #     if breadcrumbs.page() > 1:
        #         message.reactions.append(ada.emoji.PREVIOUS_PAGE)
        #     message.reactions.append(ada.emoji.INFO)
        #     if breadcrumbs.page() < self._num_pages():
        #         message.reactions.append(ada.emoji.NEXT_PAGE)

        message.embed = None
        message.content = str(breadcrumbs)
        print(f"Constructing info page with start index: {breadcrumbs.start_index()}")
        message.view = MultiEntityView(self.__entities, breadcrumbs.start_index(), self.__processor)
        return [message]

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        if len(self.__entities) == 0:
            message = ResultMessage()
            message.embed = Embed(title="No matches found")
            message.content = str(breadcrumbs)
            return [message]
        if len(self.__entities) > 1:
            return self._get_info_page(breadcrumbs)

        breadcrumbs.replace_primary_query(self.__entities[0].var())
        message = ResultMessage()
        message.embed = self.__entities[0].embed()
        message.view = self.__entities[0].view(self.__processor)
        message.content = str(breadcrumbs)
        message.reactions = [ada.emoji.PREVIOUS_PAGE]
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        pass
        # query = None
        # if emoji == ada.emoji.INFO:
        #     self.__add_reaction_selectors = True
        # elif emoji == ada.emoji.PREVIOUS_PAGE and breadcrumbs.has_prev_query():
        #     breadcrumbs.goto_prev_query()
        #     query = breadcrumbs.primary_query()
        # elif emoji == ada.emoji.NEXT_PAGE and breadcrumbs.page() < self._num_pages():
        #     breadcrumbs.goto_next_page()
        # elif emoji == ada.emoji.PREVIOUS_PAGE and breadcrumbs.page() > 1:
        #     breadcrumbs.goto_prev_page()
        # elif emoji in ada.emoji.NUM_EMOJI:
        #     index = ada.emoji.NUM_EMOJI.index(emoji) - 1
        #     selected_var = self._get_var_on_page(breadcrumbs.page(), index)
        #     query = selected_var.human_readable_name()
        #     breadcrumbs.add_query(query)
        # return query
