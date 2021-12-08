from __future__ import annotations

from typing import List


class BreadcrumbsException(Exception):
    pass


class Breadcrumbs:
    def __init__(self, queries: List[str], page: int) -> None:
        self._queries = queries
        self._page = page

    def __str__(self) -> str:
        return "```" + str(self._page) + "\n" + " > ".join(self._queries) + "\n```"

    def primary_query(self):
        return self._queries[-1]

    def page(self):
        return self._page

    def goto_next_page(self):
        self._page += 1

    def goto_prev_page(self):
        self._page -= 1

    def add_query(self, query):
        self._queries.append(query)

    def has_prev_query(self):
        return len(self._queries) > 1

    def goto_prev_query(self):
        self._queries.pop()

    @classmethod
    def extract(cls, content):
        content_lines = content.splitlines()
        if len(content_lines) <= 2:
            raise BreadcrumbsException(
                "Content only had " + str(len(content_lines)) + " lines"
            )
        if not content_lines[0].startswith("```") or not content_lines[2].startswith(
            "```"
        ):
            raise BreadcrumbsException(
                "Content missing code section:\n" + str(content_lines)
            )
        if not content_lines[0][3:].isdigit():
            raise BreadcrumbsException(
                "Page was not a digit: "
                + content_lines[0][3:]
                + " content:\n"
                + str(content_lines)
            )
        page = int(content_lines[0][3:])
        query_line = content_lines[1]
        queries = [x.strip() for x in query_line.split(">")]
        return cls(queries, page)

    @classmethod
    def create(cls, query: str) -> Breadcrumbs:
        return cls(queries=[query], page=1)
