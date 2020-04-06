from discord import Embed
import image_fetcher


class Generator:
    def __init__(self, building_data, generator_data, db):
        self.__building_data = building_data
        self.__generator_data = generator_data

        self.__fuel_items = []
        for item_class_name in generator_data["fuel"]:
            self.__fuel_items.append(db.item_from_class_name(item_class_name))

    def var(self):
        return "generator:" + self.__building_data["slug"]

    def human_readable_name(self):
        return self.__building_data["name"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(' ', '_')

    def power_production(self):
        return self.__generator_data["powerProduction"]

    def fuel_items(self):
        return self.__fuel_items

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  power production: " +
                   str(self.power_production()) + " MW")
        out.append("  fuel types:")
        for fuel_item in self.__fuel_items:
            out.append("    " + fuel_item.human_readable_name())
        out.append(self.__building_data["description"])
        out.append("")
        return '\n'.join(out)

    def wiki(self):
        return "https://satisfactory.gamepedia.com/" + self.human_readable_underscored()

    def thumb(self):
        print(image_fetcher.fetch_first_on_page(self.wiki()))
        return image_fetcher.fetch_first_on_page(self.wiki())

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = self.__generator_data["description"]
        embed.url = self.wiki()
        embed.set_thumbnail(url=self.thumb())
        embed.add_field(name="Power Production", value=(
            str(self.power_production()) + " MW"))
        # TODO
        return embed
