from discord import Embed
import ada.image_fetcher

STACK_SIZES = {
    "SS_HUGE": 500,
    "SS_BIG": 200,
    "SS_MEDIUM": 100,
    "SS_SMALL": 50,
    "SS_FLUID": 50,
}

class Item:
    def __init__(self, data, is_resource):
        self.__data = data
        self.__is_resource = is_resource

    def slug(self):
        return self.__data["mDisplayName"].lower().replace(' ', '-')

    def var(self):
        if self.__is_resource:
            return "resource:" + self.slug()
        return "item:" + self.slug()

    def class_name(self):
        return self.__data["ClassName"]

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
        return ''.join(i for i in self.__data["mDisplayName"] if ord(i) < 128)

    def human_readable_underscored(self):
        return self.human_readable_name().replace(' ', '_')

    def energy_value(self):
        if self.is_liquid():
            return float(self.__data["mEnergyValue"]) * 1000
        return float(self.__data["mEnergyValue"])

    def stack_size(self):
        if self.__data["mStackSize"].isdigit():
            return int(self.__data["mStackSize"])
        if self.__data["mStackSize"] in STACK_SIZES:
            return STACK_SIZES[self.__data["mStackSize"]]
        return -1
        

    def is_resource(self):
        return self.__is_resource

    def is_liquid(self):
        return self.__data["mForm"] == "RF_LIQUID"

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  stack size: " + str(self.stack_size()))
        out.append("  sink value: " + str(self.__data["mResourceSinkPoints"]))
        out.append(self.__data["mDescription"])
        out.append("")
        return '\n'.join(out)

    def wiki(self):
        return "https://satisfactory.gamepedia.com/" + self.human_readable_underscored()

    def thumb(self):
        print(ada.image_fetcher.fetch_first_on_page(self.wiki()))
        return ada.image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["mDescription"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(name="Stack Size", value=str(self.stack_size()), inline=True)
        embed.add_field(name="Sink Value",
                        value=str(self.__sink_value), inline=True)
        return embed
