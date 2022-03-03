from typing import Any, List, Union

from ada import image_fetcher
from ada.db.item import Item
from discord import Embed


class PowerGenerator:
    def __init__(self, data, items):
        self.__data = data
        self.__fuel_items = []
        if "mDefaultFuelClasses" not in data:
            return
        for fuel_class in data["mDefaultFuelClasses"][1:-1].split(","):
            fuel_class_short = fuel_class.split(".")[1]
            fuel_items = [
                item for item in items if item.native_class_name() == fuel_class_short
            ]
            if fuel_items:
                # This fuel class is something generic, like 'FGItemDescriptorBiomass' which describes
                # all biomass items.
                self.__fuel_items.extend(fuel_items)
            else:
                # This fuel class is a specific item, so find it by its class name.
                for item in items:
                    if item.class_name() == fuel_class_short:
                        self.__fuel_items.append(item)

    def var(self) -> str:
        return "generator:" + self.__data["mDisplayName"].lower().replace(" ", "-")

    def human_readable_name(self):
        return self.__data["mDisplayName"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(" ", "_")

    def power_production(self) -> float:
        return float(self.__data["mPowerProduction"])

    def fuel_items(self) -> List[Union[Any, Item]]:
        return self.__fuel_items

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  power production: " + str(self.power_production()) + " MW")
        out.append("  fuel types:")
        for fuel_item in self.__fuel_items:
            out.append("    " + fuel_item.human_readable_name())
        out.append(self.__data["mDescription"])
        out.append("")
        return "\n".join(out)

    def wiki(self):
        return (
            "https://satisfactory.fandom.com/wiki/" + self.human_readable_underscored()
        )

    def thumb(self):
        print(image_fetcher.fetch_first_on_page(self.wiki()))
        return image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["mDescription"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(
            name="Power Production", value=(str(self.power_production()) + " MW")
        )
        # TODO
        return embed