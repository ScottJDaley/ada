from __future__ import annotations

from typing import List


class BreadcrumbsException(Exception):
    pass


class Breadcrumbs:
    def __init__(self, queries: List[str], start_index: int) -> None:
        self.__queries = queries
        self.__start_index = start_index

    def __str__(self) -> str:
        return "```" + str(self.__start_index) + "\n" + " > ".join(self.__queries) + "\n```"

    def primary_query(self):
        return self.__queries[-1]

    def start_index(self):
        return self.__start_index

    def set_start_index(self, index: int):
        self.__start_index = index

    def add_query(self, query):
        self.set_start_index(0)
        self.__queries.append(query)

    def has_prev_query(self):
        return len(self.__queries) > 1

    def goto_prev_query(self):
        self.set_start_index(0)
        self.__queries.pop()

    def replace_primary_query(self, query):
        self.goto_prev_query()
        self.add_query(query)

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
        start_index = int(content_lines[0][3:])
        query_line = content_lines[1]
        queries = [x.strip() for x in query_line.split(">")]
        return cls(queries, start_index)

    @classmethod
    def create(cls, query: str) -> Breadcrumbs:
        return cls(queries=[query], start_index=0)
