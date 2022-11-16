from typing import Dict

import ada.image_fetcher
from discord import Embed


class Extractor:
    def __init__(self, data: Dict[str, str]) -> None:
        self.__data = data

    def var(self) -> str:
        return "extractor:" + self.__data["mDisplayName"].lower().replace(" ", "-")

    def class_name(self) -> str:
        return self.__data["ClassName"]

    def human_readable_name(self) -> str:
        return self.__data["mDisplayName"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(" ", "_")

    def power_consumption(self) -> float:
        return float(self.__data["mPowerConsumption"])

    def minute_rate(self) -> float:
        raw_minute_rate = (
            60
            * float(self.__data["mItemsPerCycle"])
            / float(self.__data["mExtractCycleTime"])
        )
        if self.is_liquid_extractor():
            return raw_minute_rate / 1000
        return raw_minute_rate

    def is_liquid_extractor(self) -> bool:
        return "RF_LIQUID" in self.__data["mAllowedResourceForms"]

    def details(self):
        out = [
            self.human_readable_name(),
            "  var: " + self.var(),
            "  power consumption: " + str(self.power_consumption()) + " MW",
            "  extraction rate: " + str(self.minute_rate()) + "/min",
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
        embed.add_field(
            name="Extraction Rate", value=(str(self.minute_rate()) + "/min")
        )
        # TODO
        return embed
