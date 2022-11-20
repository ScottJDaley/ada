from abc import ABC, abstractmethod

import discord

from ada.processor import Processor


class Entity(ABC):
    @abstractmethod
    def var(self) -> str:
        pass

    @abstractmethod
    def human_readable_name(self) -> str:
        pass

    @abstractmethod
    def embed(self) -> discord.Embed:
        pass

    @abstractmethod
    def view(self, processor: Processor) -> discord.ui.View:
        pass
