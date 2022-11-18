from __future__ import annotations

from typing import List


class BreadcrumbsException(Exception):
    pass


class Breadcrumbs:
    def __init__(self, queries: List[str], custom_id: str) -> None:
        self.__queries = queries
        self.__custom_id = custom_id

    def __str__(self) -> str:
        return "```" + self.__custom_id + "\n" + " > ".join(self.__queries) + "\n```"

    def primary_query(self):
        return self.__queries[-1]

    def custom_id(self):
        return self.__custom_id

    def set_custom_id(self, custom_id: str):
        self.__custom_id = custom_id

    def clear_custom_id(self):
        self.__custom_id = ""

    def add_query(self, query):
        self.clear_custom_id()
        self.__queries.append(query)

    def has_prev_query(self):
        return len(self.__queries) > 1

    def goto_prev_query(self):
        self.clear_custom_id()
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
        custom_id = content_lines[0][3:]
        query_line = content_lines[1]
        queries = [x.strip() for x in query_line.split(">")]
        return cls(queries, custom_id)

    @classmethod
    def create(cls, query: str) -> Breadcrumbs:
        return cls(queries=[query], custom_id="")
