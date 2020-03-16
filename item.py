

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
        return "item-" + self.slug()

    def human_readable_name(self):
        return self.__data["name"]

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