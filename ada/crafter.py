from discord import Embed
import ada.image_fetcher


class Crafter:
    def __init__(self, data):
        self.__data = data

    def var(self):
        return "crafter:" + self.__data["mDisplayName"].lower().replace(' ', '-')
    
    def class_name(self):
        return self.__data["ClassName"]

    def human_readable_name(self):
        return self.__data["mDisplayName"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(' ', '_')

    def power_consumption(self):
        return float(self.__data["mPowerConsumption"])

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  power consumption: " +
                   str(self.power_consumption()) + " MW")
        out.append(self.__data["mDescription"])
        out.append("")
        return '\n'.join(out)

    def wiki(self):
        return "https://satisfactory.fandom.com/wiki/" + self.human_readable_underscored()

    def thumb(self):
        print(ada.image_fetcher.fetch_first_on_page(self.wiki()))
        return ada.image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["mDescription"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(name="Power Consumption", value=(
            str(self.power_consumption()) + " MW"))
        # TODO
        return embed
