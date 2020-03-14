

class Building:
    def __init__(self, data):
        self.__data = data

    def var(self):
        return "building:" + self.__data["slug"]

    def human_readable_name(self):
        return self.__data["name"]

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  power consumption: " + str(self.__data["metadata"]["powerConsumption"]) + " MW")
        out.append(self.__data["description"])
        out.append("")
        return '\n'.join(out)