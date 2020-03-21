from discord import Embed
import image_fetcher


class Item:
    def __init__(self, data, is_resource):
        self.__data = data
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

    class InputVariable:
        def __init__(self, item):
            self.item = item

        def var(self):
            return self.item.var() + ":input"

        def human_readable_name(self):
            return self.item.human_readable_name()

        def viz_name(self):
            return self.item.viz_name() + "-input"

        def viz_label(self, amount):
            out = '<'
            out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
            out += '<TR>'
            out += '<TD COLSPAN="2" BGCOLOR="moccasin">' + \
                str(round(amount, 2)) + '/m'
            out += '<BR/>' + self.item.human_readable_name() + '</TD>'
            out += '</TR>'
            out += '</TABLE>>'
            return out

    def input(self):
        return self.InputVariable(self)

    class OutputVariable:
        def __init__(self, item):
            self.item = item

        def var(self):
            return self.item.var() + ":output"

        def human_readable_name(self):
            return self.item.human_readable_name()

        def viz_name(self):
            return self.item.viz_name() + "-output"

        def viz_label(self, amount):
            out = '<'
            out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
            out += '<TR>'
            out += '<TD COLSPAN="2" BGCOLOR="lightblue">' + \
                str(round(amount, 2)) + '/m'
            out += '<BR/>' + self.human_readable_name() + '</TD>'
            out += '</TR>'
            out += '</TABLE>>'
            return out

    def output(self):
        return self.OutputVariable(self)

    def human_readable_name(self):
        return self.__data["name"]

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
        out.append(self.__data["description"])
        out.append("")
        return '\n'.join(out)

    def wiki(self):
        return "https://satisfactory.gamepedia.com/" + self.human_readable_underscored()

    def thumb(self):
        print(image_fetcher.fetch_first_on_page(self.wiki()))
        return image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        # {
        #     "content": "```item:iron-ingot```",
        #     "embed": {
        #         "title": "Iron Ingot",
        #         "description": "Used for crafting.\nCrafted into the most basic parts.",
        #         "url": "https://satisfactory.gamepedia.com/Iron_Ingot",
        #         "thumbnail": {
        #         "url": "https://gamepedia.cursecdn.com/satisfactory_gamepedia_en/thumb/0/0a/Iron_Ingot.png/120px-Iron_Ingot.png"
        #         },
        #         "fields": [
        #         {
        #             "name": "stack size",
        #             "value": "100"
        #         },
        #         {
        #             "name": "sink value",
        #             "value": "2"
        #         }
        #         ]
        #     }
        # }
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__data["description"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        # embed.thumbnail.url = "https://gamepedia.cursecdn.com/satisfactory_gamepedia_en/thumb/0/0a/" + \
        #     underscored_name + ".png/120px-" + underscored_name + ".png"
        # embed.thumbnail.width = 120
        # embed.thumbnail.height = 120
        # print("https://gamepedia.cursecdn.com/satisfactory_gamepedia_en/thumb/0/0a/" +
        #       underscored_name + ".png/120px-" + underscored_name + ".png")

        embed.add_field(name="Stack Size", value=str(
            self.__data["stackSize"]), inline=True)
        embed.add_field(name="Sink Value",
                        value="TODO", inline=True)
        return embed
