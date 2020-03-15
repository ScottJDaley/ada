

class PowerRecipe:
    def __init__(self, fuel_item, generator):
        # item var => recipe item
        self.__fuel_item = fuel_item
        self.__generator = generator

    def var(self):
        return "power-recipe:" + self.__fuel_item.slug()

    def viz_name(self):
        return "power-recipe-" + self.__fuel_item.slug()

    def human_readable_name(self):
        return "Power Recipe: " + self.__fuel_item.human_readable_name()

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  generator: " + self.__generator.human_readable_name())
        out.append("  fuel:")
        out.append("    " + self.fuel_minute_rate() + " " + self.__fuel_item.human_readable_name() + "/m")
        out.append("  power:")
        out.append("    " + self.__generator.power_production())
        out.append("")
        return '\n'.join(out)

    def fuel_minute_rate(self):
         # Example:
        # 75 MW power production from generator
        # = 75 MJ/s
        # = 75 * 60 = 4500 MJ/m
        # 300 MJ energy value of coal
        # 4500 MJ/m / 300 MJ/coal = 15 coal/m
        return self.__generator.power_production() * 60 / self.__fuel_item.energy_value()

    def power_production(self):
        return self.__generator.power_production()

    def fuel_item(self):
        return self.__fuel_item

    def generator(self):
        return self.__generator