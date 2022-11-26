import re
from typing import Dict, Optional

from .entity import Entity
from ..utils import image_fetcher

STACK_SIZES = {
    "SS_HUGE": 500,
    "SS_BIG": 200,
    "SS_MEDIUM": 100,
    "SS_SMALL": 50,
    "SS_FLUID": 50,
}


class Item(Entity):
    def __init__(
            self, data: Dict[str, str], native_class_name: str, is_resource: bool
    ) -> None:
        self.__data = data
        self.__native_class_name = native_class_name
        self.__is_resource = is_resource

    def slug(self) -> str:
        display_name = self.__data["mDisplayName"]
        if display_name:
            slug = self.__data["mDisplayName"].lower().replace(" ", "-")
        else:
            slug = self.class_name().removesuffix("_C").removeprefix("Build_").replace("_", "-")
            slug = re.sub(r'(?<!^)(?=[A-Z])', '-', slug).lower()
            slug = re.sub(r'\-+', '-', slug)
        return slug

    def var(self) -> str:
        return "item:" + self.slug()

    def class_name(self) -> str:
        return self.__data["ClassName"]

    def native_class_name(self) -> str:
        return self.__native_class_name

    def viz_name(self) -> str:
        return "item-" + self.slug()

    def viz_label(self, amount: float) -> str:
        color = "moccasin" if amount < 0 else "lightblue"
        out = "<"
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        out += "<TR>"
        out += (
                '<TD COLSPAN="2" BGCOLOR="'
                + color
                + '">'
                + str(round(abs(amount), 2))
                + "/m"
        )
        out += "<BR/>" + self.human_readable_name() + "</TD>"
        out += "</TR>"
        out += "</TABLE>>"
        return out

    def human_readable_name(self) -> str:
        display_name = self.__data["mDisplayName"]
        if not display_name:
            display_name = self.class_name().removesuffix("_C").removeprefix("Desc_").replace("_", " ")
            display_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', display_name)
            display_name = re.sub(r' +', ' ', display_name)
        return "".join(i for i in display_name if ord(i) < 128)

    def human_readable_underscored(self) -> str:
        return self.human_readable_name().replace(" ", "_")

    def energy_value(self) -> float:
        if self.is_liquid():
            return float(self.__data["mEnergyValue"]) * 1000
        return float(self.__data["mEnergyValue"])

    def stack_size(self) -> int:
        if self.__data["mStackSize"].isdigit():
            return int(self.__data["mStackSize"])
        if self.__data["mStackSize"] in STACK_SIZES:
            return STACK_SIZES[self.__data["mStackSize"]]
        return -1

    def sink_value(self) -> Optional[int]:
        return int(self.__data["mResourceSinkPoints"]) if "mResourceSinkPoints" in self.__data else None

    def is_resource(self) -> bool:
        return self.__is_resource

    def is_liquid(self) -> bool:
        return self.__data["mForm"] == "RF_LIQUID"

    def description(self):
        return self.__data["mDescription"]

    def details(self):
        out = [
            self.human_readable_name(),
            "  var: " + self.var(),
            "  stack size: " + str(self.stack_size()),
            "  sink value: " + str(self.sink_value()),
            self.description(),
            ""
        ]
        return "\n".join(out)

    def wiki(self) -> str:
        return (
                "https://satisfactory.fandom.com/wiki/" + self.human_readable_underscored()
        )

    def thumb(self) -> str:
        print(image_fetcher.fetch_first_on_page(self.wiki()))
        return image_fetcher.fetch_first_on_page(self.wiki())

    def fields(self) -> list[tuple[str, str]]:
        return [
            ("Stack Size", str(self.stack_size())),
            ("Sink Value", str(self.sink_value())),
        ]

    # def embed(self) -> discord.Embed:
    #     embed = discord.Embed(title=self.human_readable_name())
    #     embed.description = self.__data["mDescription"]
    #     embed.url = self.wiki()
    #     embed.set_thumbnail(url=self.thumb())
    #     embed.add_field(name="Stack Size", value=str(self.stack_size()), inline=True)
    #     embed.add_field(name="Sink Value", value=str(self.sink_value()), inline=True)
    #     return embed
    #
    # def view(self, dispatch: ada.Dispatch) -> discord.ui.View:
    #     return ada.views.ItemView(dispatch)
