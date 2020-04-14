from discord import Embed
import ada.image_fetcher


class Item:
    def __init__(self, data, sink_value, is_resource):
        self.__data = data
        self.__sink_value = sink_value
        self.__is_resource = is_resource

    def slug(self):
        return self.__data["slug"]

    def var(self):
        if self.__is_resource:
            return "resource:" + self.slug()
        return "item:" + self.slug()

    def viz_name(self):
        if self.__is_resource:
            return "resource-" + self.slug()
        return "item-" + self.slug()

    def viz_label(self, amount):
        color = "moccasin" if amount < 0 else "lightblue"
        out = '<'
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        out += '<TR>'
        out += '<TD COLSPAN="2" BGCOLOR="' + color + '">' + \
            str(round(abs(amount), 2)) + '/m'
        out += '<BR/>' + self.human_readable_name() + '</TD>'
        out += '</TR>'
        out += '</TABLE>>'
        return out

    def human_readable_name(self):
        return ''.join(i for i in self.__data["name"] if ord(i) < 128)

    def human_readable_underscored(self):
        return self.human_readable_name().replace(' ', '_')

    def energy_value(self):
        if self.__data["liquid"]:
            return self.__data["energyValue"] * 1000
        return self.__data["energyValue"]

    def is_resource(self):
        return self.__is_resource

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  stack size: " + str(self.__data["stackSize"]))
        out.append("  sink value: " + str(self.__sink_value))
        out.append(self.__data["description"])
        out.append("")
        return '\n'.join(out)

    def wiki(self):
        return "https://satisfactory.gamepedia.com/" + self.human_readable_underscored()

    def thumb(self):
        print(ada.image_fetcher.fetch_first_on_page(self.wiki()))
        return ada.image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["description"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(name="Stack Size", value=str(
            self.__data["stackSize"]), inline=True)
        embed.add_field(name="Sink Value",
                        value=str(self.__sink_value), inline=True)
        return embed
