from abc import ABC


class Result(ABC):
    pass


class ErrorResult(Result):
    def __init__(self, msg: str) -> None:
        self.__msg = msg

    def __str__(self):
        return self.__msg

    def error_message(self):
        return self.__msg
