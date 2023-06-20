from typing import Dict

from .entity import Entity
from ..utils import image_fetcher


class Crafter(Entity):
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

    def description(self):
        return self.__data["mDescription"]

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
                "https://satisfactory.wiki.gg/wiki/" + self.human_readable_underscored()
        )

    def thumb(self):
        print(image_fetcher.fetch_first_on_page(self.wiki()))
        return image_fetcher.fetch_first_on_page(self.wiki())

    def fields(self) -> list[tuple[str, str]]:
        return [
            ("Power Consumption", f"{self.power_consumption()} MW"),
        ]
