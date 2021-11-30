from discord import Embed
from ada.power_generator import PowerGenerator
from ada.item import Item


class PowerRecipe:
    def __init__(self, fuel_item: Item, generator: PowerGenerator) -> None:
        # item var => recipe item
        self.__fuel_item = fuel_item
        self.__generator = generator

    def var(self) -> str:
        return "power-recipe:" + self.__fuel_item.slug()

    def viz_name(self) -> str:
        return "power-recipe-" + self.__fuel_item.slug()

    def viz_label(self, amount: float) -> str:
        out = "<"
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        out += "<TR>"
        out += '<TD COLSPAN="2" BGCOLOR="lightgray">' + str(round(amount, 2)) + "x"
        out += "<BR/>" + self.generator().human_readable_name() + "</TD>"
        out += "</TR>"
        out += "<TR>"
        out += '<TD BGCOLOR="moccasin">Input</TD>'
        out += "<TD>" + self.fuel_item().human_readable_name() + "</TD>"
        out += "</TR>"
        out += "</TABLE>>"
        return out

    def human_readable_name(self):
        return "Power Recipe: " + self.__fuel_item.human_readable_name()

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  generator: " + self.__generator.human_readable_name())
        out.append("  fuel:")
        out.append(
            "    "
            + self.fuel_minute_rate()
            + " "
            + self.__fuel_item.human_readable_name()
            + "/m"
        )
        out.append("  power:")
        out.append("    " + self.__generator.power_production())
        out.append("")
        return "\n".join(out)

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        embed.description = (
            "Produces power from " + self.fuel_item().human_readable_name()
        )

        embed.add_field(
            name="Fuel Type", value=self.fuel_item().human_readable_name(), inline=True
        )
        embed.add_field(name="Fuel Rate", value=(self.fuel_minute_rate() + "/minute"))
        embed.add_field(
            name="Power", value=(self.__generator.power_production() + " MW")
        )
        return embed

    def fuel_minute_rate(self) -> float:
        # Example:
        # 75 MW power production from generator
        # = 75 MJ/s
        # = 75 * 60 = 4500 MJ/m
        # 300 MJ energy value of coal
        # 4500 MJ/m / 300 MJ/coal = 15 coal/m
        return (
            self.__generator.power_production() * 60 / self.__fuel_item.energy_value()
        )

    def power_production(self) -> float:
        return self.__generator.power_production()

    def fuel_item(self) -> Item:
        return self.__fuel_item

    def generator(self) -> PowerGenerator:
        return self.__generator
