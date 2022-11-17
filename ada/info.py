import math
from typing import List

from discord.embeds import Embed

import ada.emoji
from ada.breadcrumbs import Breadcrumbs
from ada.db.item import Item
from ada.processor import Processor
from ada.result import Result, ResultMessage


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

    def __init__(self, vars_: List[Item], raw_query: str, processor: Processor) -> None:
        self._vars = sorted(vars_, key=lambda var_: var_.human_readable_name())
        self._raw_query = raw_query
        self._add_reaction_selectors = False
        self._processor = processor

    def __str__(self):
        if len(self._vars) == 1:
            return self._vars[0].details()
        var_names = [var.human_readable_name() for var in self._vars]
        var_names.sort()
        return "\n".join(var_names)

    def _num_pages(self):
        return math.ceil(len(self._vars) / InfoResult.num_on_page)

    def _footer(self, page):
        return "Page " + str(page) + " of " + str(self._num_pages())

    def _get_var_on_page(self, page, index):
        var_index = (page - 1) * InfoResult.num_on_page + index
        return self._vars[var_index]

    def _get_info_page(self, breadcrumbs):
        var_names = [var.human_readable_name() for var in self._vars]
        start_index = (breadcrumbs.page() - 1) * InfoResult.num_on_page
        last_index = start_index + InfoResult.num_on_page

        vars_on_page = var_names[start_index:last_index]

        out = []
        message = ResultMessage()
        for i, var_ in enumerate(vars_on_page):
            prefix = ""
            if self._add_reaction_selectors:
                prefix = ada.emoji.NUM_EMOJI[i + 1]
                message.reactions.append(prefix)
            out.append("- " + prefix + var_)
        if not self._add_reaction_selectors:
            message.reactions = []
            if breadcrumbs.page() > 1:
                message.reactions.append(ada.emoji.PREVIOUS_PAGE)
            message.reactions.append(ada.emoji.INFO)
            if breadcrumbs.page() < self._num_pages():
                message.reactions.append(ada.emoji.NEXT_PAGE)

        message.embed = Embed(title=f"Found {len(self._vars)} matches:")
        message.embed.description = "\n".join(out)
        message.embed.set_footer(text=self._footer(breadcrumbs.page()))
        message.content = str(breadcrumbs)
        return [message]

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        if len(self._vars) == 0:
            message = ResultMessage()
            message.embed = Embed(title="No matches found")
            message.content = str(breadcrumbs)
            return [message]
        if len(self._vars) > 1:
            return self._get_info_page(breadcrumbs)
        message = ResultMessage()
        message.embed = self._vars[0].embed()
        message.view = self._vars[0].view(self._processor)
        message.content = str(breadcrumbs)
        message.reactions = [ada.emoji.PREVIOUS_PAGE]
        return [message]

    def handle_reaction(self, emoji, breadcrumbs):
        query = None
        if emoji == ada.emoji.INFO:
            self._add_reaction_selectors = True
        elif emoji == ada.emoji.PREVIOUS_PAGE and breadcrumbs.has_prev_query():
            breadcrumbs.goto_prev_query()
            query = breadcrumbs.primary_query()
        elif emoji == ada.emoji.NEXT_PAGE and breadcrumbs.page() < self._num_pages():
            breadcrumbs.goto_next_page()
        elif emoji == ada.emoji.PREVIOUS_PAGE and breadcrumbs.page() > 1:
            breadcrumbs.goto_prev_page()
        elif emoji in ada.emoji.NUM_EMOJI:
            index = ada.emoji.NUM_EMOJI.index(emoji) - 1
            selected_var = self._get_var_on_page(breadcrumbs.page(), index)
            query = selected_var.human_readable_name()
            breadcrumbs.add_query(query)
        return query
