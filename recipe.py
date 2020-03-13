

class Recipe:
    def __init__(self, data, db, item_from_class_name):
        self.__data = data
        self.__db = db

        self.__ingredients = {}
        self.__products = {}
        for ingredient in data["ingredients"]:
            ingredient_name = item_from_class_name[ingredient["item"]]
            self.__ingredients[ingredient_name] = ingredient["amount"]
        for product in data["products"]:
            product_name = item_from_class_name[product["item"]]
            self.__products[product_name] = product["amount"]

    def var(self):
        return "recipe:" + self.__data["slug"]

    def viz_name(self):
        return "recipe-" + self.__data["slug"]

    def human_readable_name(self):
        return "Recipe: " + self.__data["name"]

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  time: " + str(self.__data["time"]))
        out.append("  ingredients:")
        for ingredient, amount in self.__ingredients.items():
            out.append("    " + ingredient + ": " + str(amount))
        out.append("  products:")
        for product, amount in self.__products.items():
            out.append("    " + product + ": " + str(amount))
        out.append("")
        return '\n'.join(out)

    def get_ingredient_viz(self, ingredient):
        return self.__db.items()[ingredient].human_readable_name()

    def get_product_viz(self, product):
        return self.__db.items()[product].human_readable_name()
    
    def get_recipe_viz_struct(self):
        out = '{' + self.human_readable_name()
        ingredient_list = list(self.ingredients().keys())
        if len(ingredient_list) > 0:
            out += '|{'
            for ingredient in ingredient_list[:-1]:
                out += self.get_ingredient_viz(ingredient) + '|'
            out += self.get_ingredient_viz(ingredient_list[-1]) + '}'
        product_list = list(self.products().keys())
        if len(product_list) > 0:
            out += '|{'
            for product in product_list[:-1]:
                out += self.get_product_viz(product) + '|'
            out += self.get_product_viz(product_list[-1]) + '}'
        out += '}'
        return out

    def ingredients(self):
        return self.__ingredients
    
    def products(self):
        return self.__products

    def ingredient_amount(self, ingredient):
        return self.__ingredients[ingredient]

    def product_amount(self, product):
        return self.__products[product]
    
    def ingredient_minute_rate(self, ingredient):
        amount = self.ingredient_amount(ingredient)
        return 60 * amount /  self.__data["time"]

    def product_minute_rate(self, product):
        amount = self.product_amount(product)
        return 60 * amount /  self.__data["time"]