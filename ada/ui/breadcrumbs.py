from __future__ import annotations

from typing import List, Optional


class BreadcrumbsException(Exception):
    pass


class Breadcrumbs:
    def __init__(self, pages: List[Page]) -> None:
        self.__pages = pages

    def __str__(self) -> str:
        return "```\n" + "\n╰ ".join(str(page) for page in self.__pages) + "\n```"

    def format_content(self, content: Optional[str]) -> str:
        return str(self) + (f"\n{content}" if content else "")

    def current_page(self) -> Page:
        return self.__pages[-1]

    def add_page(self, page: Page) -> None:
        self.__pages.append(page)

    def has_prev_page(self) -> bool:
        return len(self.__pages) > 1

    def goto_prev_page(self) -> None:
        self.__pages.pop()

    @classmethod
    def extract(cls, content: str) -> Breadcrumbs:
        breadcrumbs, remaining_content = Breadcrumbs.parse(content)
        return breadcrumbs

    @classmethod
    def parse(cls, content: str) -> tuple[Breadcrumbs, str]:
        content_lines = content.splitlines()
        if len(content_lines) <= 2:
            raise BreadcrumbsException("Content only had " + str(len(content_lines)) + " lines")
        if not content_lines[0].startswith("```"):
            raise BreadcrumbsException("Content missing breadcrumbs start:\n" + str(content_lines))
        num_pages = 0
        found_end = False
        for line in content_lines[1:]:
            if line.startswith("```"):
                found_end = True
                break
            num_pages += 1
        if not found_end:
            raise BreadcrumbsException("Content missing breadcrumbs end:\n" + str(content_lines))

        print(f"Breadcrumbs found {num_pages} pages in:\n" + str(content_lines))
        pages = [Breadcrumbs.Page.extract(x.removeprefix("╰").strip()) for x in content_lines[1:1 + num_pages]]
        if 2 + num_pages >= len(content_lines):
            remaining_content = ""
        else:
            remaining_content = "\n".join(content_lines[2 + num_pages:])
        return cls(pages), remaining_content

    @classmethod
    def create(cls, query: str, custom_ids: list[str] = None) -> Breadcrumbs:
        page = Breadcrumbs.Page(query, custom_ids)
        return cls([page])

    class Page:
        def __init__(self, query: str, custom_ids: list[str] = None):
            self.__query = query
            self.__custom_ids = custom_ids if custom_ids else []

        def __str__(self) -> str:
            result = self.__query
            if len(self.__custom_ids) > 0:
                result += f" [{' '.join(self.__custom_ids)}]"
            return result

        def query(self) -> str:
            return self.__query

        def replace_query(self, query: str) -> None:
            self.__query = query

        def custom_ids(self) -> list[str]:
            return self.__custom_ids

        def add_custom_id(self, custom_id: str):
            self.__custom_ids.append(custom_id)

        def clear_custom_ids(self) -> None:
            self.__custom_ids = []

        def set_custom_ids(self, custom_ids: list[str]) -> None:
            self.__custom_ids = custom_ids if custom_ids else []

        def set_single_custom_id(self, custom_id: str) -> None:
            self.__custom_ids = [custom_id]

        @classmethod
        def extract(cls, content: str) -> Breadcrumbs.Page:
            custom_ids_start = content.find("[")
            if custom_ids_start < 0:
                return cls(content)
            query = content[:custom_ids_start].strip()
            custom_ids = content[custom_ids_start + 1:-1].strip().split(" ")
            return cls(query, custom_ids)
