from discord import Embed
import ada.image_fetcher


def parse_list(raw):
    return raw[1:-1].split(",")


class Generator:
    def __init__(self, data, db):
        self.__data = data

        self.__fuel_items = []
        if "mDefaultFuelClasses" not in data:
            return
        for fuel_class in parse_list(data["mDefaultFuelClasses"]):
            fuel_class_name = fuel_class.split(".")[1]
            fuel_items = db.items_from_native_class_name(fuel_class_name)
            if fuel_items is not None:
                self.__fuel_items.extend(fuel_items)
            else:
                self.__fuel_items.append(db.item_from_class_name(fuel_class_name))

    def var(self):
        return "generator:" + self.__data["mDisplayName"].lower().replace(" ", "-")

    def human_readable_name(self):
        return self.__data["mDisplayName"]

    def human_readable_underscored(self):
        return self.human_readable_name().replace(" ", "_")

    def power_production(self):
        return float(self.__data["mPowerProduction"])

    def fuel_items(self):
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
        print(ada.image_fetcher.fetch_first_on_page(self.wiki()))
        return ada.image_fetcher.fetch_first_on_page(self.wiki())

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
