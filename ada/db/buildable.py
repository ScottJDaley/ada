from typing import Dict

import ada.image_fetcher
from discord import Embed


class Buildable:
    def __init__(self, data: Dict[str, str], native_class_name: str) -> None:
        self.__data = data
        self.__native_class_name = native_class_name

    def slug(self) -> str:
        slug = self.__data["mDisplayName"].lower().replace(" ", "-")
        if "_Metal_" in self.__data["ClassName"]:
            slug += "-metal"
        if "_Polished_" in self.__data["ClassName"]:
            slug += "-polished"
        if "_Concrete_" in self.__data["ClassName"]:
            slug += "-concrete"
        if "_ConcretePolished_" in self.__data["ClassName"]:
            slug += "-concrete-polished"
        if "_Steel_" in self.__data["ClassName"]:
            slug += "-steel"
        return slug

    def var(self) -> str:
        return "buildable:" + self.slug()

    def class_name(self) -> str:
        return self.__data["ClassName"]

    def native_class_name(self) -> str:
        return self.__native_class_name

    def human_readable_name(self) -> str:
        return "".join(i for i in self.__data["mDisplayName"] if ord(i) < 128)

    def human_readable_underscored(self) -> str:
        return self.human_readable_name().replace(" ", "_")

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append(self.__data["mDescription"])
        out.append("")
        return "\n".join(out)

    def wiki(self) -> str:
        return (
            "https://satisfactory.fandom.com/wiki/" + self.human_readable_underscored()
        )

    def thumb(self) -> str:
        print(ada.image_fetcher.fetch_first_on_page(self.wiki()))
        return ada.image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self) -> Embed:
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["mDescription"]
        embed.url = self.wiki()
        if self.thumb():
            embed.set_thumbnail(url=self.thumb())
        return embed
