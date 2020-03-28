

class Recipe:
    class RecipeItem:
        def __init__(self, item, amount, time):
            self.__item = item
            self.__amount = amount
            self.__time = time

        def item(self):
            return self.__item

        def amount(self):
            return self.__amount

        def minute_rate(self):
            return 60 * self.amount() / self.__time

        def human_readable_name(self):
            return self.item().human_readable_name() + ": " + str(self.amount()) + " (" + str(self.minute_rate()) + "/m)"

    def __init__(self, data, db):
        self.__data = data
        self.__db = db

        # item var => recipe item
        self.__ingredients = {}
        self.__products = {}
        for ingredient in data["ingredients"]:
            item = db.item_from_class_name(ingredient["item"])
            self.__ingredients[item.var()] = self.RecipeItem(
                item, ingredient["amount"], data["time"])
        for product in data["products"]:
            item = db.item_from_class_name(product["item"])
            self.__products[item.var()] = self.RecipeItem(
                item, product["amount"], data["time"])
        # if len(self.__products) > 1:
        #     print("Found multi-product recipe:", self.var())
        #     print("  ", self.__products.keys())
        self.__crafter = db.crafter_from_class_name(data["producedIn"][0])

    def var(self):
        return "recipe:" + self.__data["slug"]

    def viz_name(self):
        return "recipe-" + self.__data["slug"]

    def viz_label(self, amount):
        out = '<'
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        out += '<TR>'
        out += '<TD COLSPAN="2" BGCOLOR="lightgray">' + \
            str(round(amount, 2)) + 'x'
        out += '<BR/>' + self.human_readable_name() + '</TD>'
        out += '</TR>'
        for ingredient in self.ingredients().values():
            out += '<TR>'
            out += '<TD BGCOLOR="moccasin">Input</TD>'
            out += '<TD>' + ingredient.item().human_readable_name() + '</TD>'
            out += '</TR>'
        for product in self.products().values():
            out += '<TR>'
            out += '<TD BGCOLOR="lightblue">Output</TD>'
            out += '<TD>' + product.item().human_readable_name() + '</TD>'
            out += '</TR>'
        out += '</TABLE>>'
        return out

    def human_readable_name(self):
        return "Recipe: " + self.__data["name"]

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  time: " + str(self.__data["time"]) + "s")
        out.append("  crafted in: " + self.crafter().human_readable_name())
        out.append("  ingredients:")
        for ingredient in self.__ingredients.values():
            out.append("    " + ingredient.human_readable_name())
        out.append("  products:")
        for product in self.__products.values():
            out.append("    " + product.human_readable_name())
        out.append("")
        return '\n'.join(out)

    def ingredients(self):
        return self.__ingredients

    def products(self):
        return self.__products

    def ingredient(self, var):
        return self.__ingredients[var]

    def product(self, var):
        return self.__products[var]

    def crafter(self):
        return self.__crafter

    def is_alternate(self):
        return self.__data["alternate"]
