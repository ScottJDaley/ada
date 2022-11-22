from abc import ABC, abstractmethod


class Entity(ABC):
    @abstractmethod
    def var(self) -> str:
        pass

    @abstractmethod
    def human_readable_name(self) -> str:
        pass

    @abstractmethod
    def description(self):
        pass

    @abstractmethod
    def fields(self) -> list[tuple[str, str]]:
        pass
