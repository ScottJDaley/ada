

class Recipe:
    def __init__(self, data, db):
        self.__data = data
        self.__db = db

    def var(self):
        return "recipe:" + self.__data["slug"]

    def human_readable_name(self):
        return "Recipe: " + self.__data["name"]

    def details(self):
        print("RECIPE DETAILS")
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  time: " + str(self.__data["time"]))
        out.append("  ingredients:")
        for ingredient in self.__data["ingredients"]:
            out.append("    " + self.__db.item_from_class_name(ingredient["item"]) + ": " + str(ingredient["amount"]))
        out.append("  products:")
        for product in self.__data["products"]:
            out.append("    " + self.__db.item_from_class_name(product["item"]) + ": " + str(product["amount"]))
        out.append("")
        return '\n'.join(out)