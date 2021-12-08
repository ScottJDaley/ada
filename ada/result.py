from abc import ABCMeta, abstractclassmethod
from typing import List

from discord import Embed

from ada.breadcrumbs import Breadcrumbs


class ResultMessage:
    def __init__(self) -> None:
        self.content = None
        self.embed = None
        self.file = None
        self.reactions = []


class Result(metaclass=ABCMeta):
    @abstractclassmethod
    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        raise NotImplementedError

    @abstractclassmethod
    def handle_reaction(self, emoji: str, breadcrumbs: Breadcrumbs) -> str:
        return NotImplementedError


class ErrorResult(Result):
    def __init__(self, msg: str) -> None:
        self.__msg = msg

    def __str__(self):
        return self.__msg

    def messages(self, breadcrumbs: Breadcrumbs) -> List[ResultMessage]:
        message = ResultMessage()
        message.embed = Embed(title="Error")
        message.embed.description = self.__msg
        message.content = str(breadcrumbs)
        return [message]

    def handle_reaction(self, emoji: str, breadcrumbs: Breadcrumbs):
        return None
