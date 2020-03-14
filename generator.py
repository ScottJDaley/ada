# generators:

# "Build_GeneratorCoal_C": {
#     "className": "Build_GeneratorCoal_C",
#     "fuel": [
#         "Desc_Coal_C",
#         "Desc_CompactedCoal_C",
#         "Desc_PetroleumCoke_C"
#     ],
#     "powerProduction": 75,
#     "powerProductionExponent": 1.3
# },

# buildings:

# "Desc_GeneratorCoal_C": {
#     "slug": "coal-generator",
#     "name": "Coal Generator",
#     "description": "Burns coal to generate electricity for your power grid.\nHas an input so feeding coal can be automated.",
#     "categories": [
#         "SC_Generators_C"
#     ],
#     "buildMenuPriority": 21,
#     "className": "Desc_GeneratorCoal_C",
#     "metadata": {
#         "powerConsumption": 0,
#         "powerConsumptionExponent": 1.6
#     }
# },

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

    def power_production(self):
        return self.__generator_data["powerProduction"]

    def fuel_items(self):
        return self.__fuel_items

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  power production: " + str(self.power_production()) + " MW")
        out.append("  fuel types:")
        for fuel_item in self.__fuel_items:
            out.append("    " + fuel_item.human_readable_name())
        out.append(self.__building_data["description"])
        out.append("")
        return '\n'.join(out)