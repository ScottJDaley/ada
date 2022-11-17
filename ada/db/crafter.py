from typing import Dict

import discord

import ada.image_fetcher
from discord import Embed

from ada.processor import Processor
from ada.views.crafter_view import CrafterView


class Crafter:
    def __init__(self, data: Dict[str, str]) -> None:
        self.__data = data

    def var(self) -> str:
        return "crafter:" + self.__data["mDisplayName"].lower().replace(" ", "-")

    def class_name(self) -> str:
        return self.__data["ClassName"]

    def human_readable_name(self) -> str:
        return self.__data["mDisplayName"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(" ", "_")

    def power_consumption(self) -> float:
        return float(self.__data["mPowerConsumption"])

    def details(self):
        out = [
            self.human_readable_name(),
            "  var: " + self.var(),
            "  power consumption: " + str(self.power_consumption()) + " MW",
            self.__data["mDescription"],
            ""
        ]
        return "\n".join(out)

    def wiki(self):
        return (
            "https://satisfactory.fandom.com/wiki/" + self.human_readable_underscored()
        )

    def thumb(self):
        print(ada.image_fetcher.fetch_first_on_page(self.wiki()))
        return ada.image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["mDescription"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(
            name="Power Consumption", value=(str(self.power_consumption()) + " MW")
        )
        # TODO
        return embed

    @staticmethod
    def view(processor: Processor) -> discord.ui.View:
        return CrafterView(processor)
