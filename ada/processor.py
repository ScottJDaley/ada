from abc import ABC, abstractmethod
from ada.result import Result


class Processor(ABC):
    @abstractmethod
    async def do(
        self, raw_query: str
    ) -> Result:
        pass

    @abstractmethod
    def lookup(self, var: str):
        pass
