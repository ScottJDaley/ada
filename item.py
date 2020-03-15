

class Item:
    def __init__(self, data, prefix):
        self.__data = data
        self.__prefix = prefix

    def slug(self):
        return self.__data["slug"]

    def var(self):
        return self.__prefix + ":" + self.slug()

    def input_var(self):
        return self.var() + ":input"
    
    def output_var(self):
        return self.var() + ":output"

    def human_readable_name(self):
        return self.__data["name"]

    def energy_value(self):
        if self.__data["liquid"]:
            return self.__data["energyValue"] * 1000
        return self.__data["energyValue"]
    
    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  stack size: " + str(self.__data["stackSize"]))
        out.append(self.__data["description"])
        out.append("")
        return '\n'.join(out)