from discord import Embed
import image_fetcher


class Crafter:
    def __init__(self, data):
        self.__data = data

    def var(self):
        return "crafter:" + self.__data["slug"]

    def human_readable_name(self):
        return self.__data["name"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(' ', '_')

    def power_consumption(self):
        return self.__data["metadata"]["powerConsumption"]

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  power consumption: " +
                   str(self.power_consumption()) + " MW")
        out.append(self.__data["description"])
        out.append("")
        return '\n'.join(out)

    def wiki(self):
        return "https://satisfactory.gamepedia.com/" + self.human_readable_underscored()

    def thumb(self):
        print(image_fetcher.fetch_first_on_page(self.wiki()))
        return image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["description"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(name="Power Consumption", value=(
            str(self.power_consumption()) + " MW"))
        # TODO
        return embed
