from discord import Embed

def parse_list(raw):
    if raw.startswith('(('):
        return raw[2:-2].split('),(')
    return [raw[1:-1]]

def parse_recipe_item(raw):
    components = raw.split(',')
    component_map = {}
    for component in components:
        key_value = component.split('=')
        component_map[key_value[0]] = key_value[1]
    class_name = component_map['ItemClass'].split('.')[1][:-2]
    return class_name, int(component_map['Amount'])

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
            return self.item().human_readable_name() + ": " + \
                str(self.amount()) + " (" + str(self.minute_rate()) + "/m)"

    def __init__(self, data, db):
        self.__data = data
        self.__db = db

        self.__crafter = None
        if len(data["mProducedIn"]) == 0:
            return
        producers = parse_list(data["mProducedIn"])
        for producer in producers:
            producer_class_name = producer.split('.')[1]
            crafter = db.crafter_from_class_name(producer_class_name)
            if crafter is not None:
                self.__crafter = crafter
        if self.__crafter is None:
            return

        # item var => recipe item
        self.__ingredients = {}
        self.__products = {}
        for ingredient in parse_list(data["mIngredients"]):
            class_name, amount = parse_recipe_item(ingredient)
            item = db.item_from_class_name(class_name)
            if item.is_liquid():
                amount = int(amount / 1000)
            self.__ingredients[item.var()] = self.RecipeItem(
                item, amount, float(data["mManufactoringDuration"]))
        for product in parse_list(data["mProduct"]):
            class_name, amount = parse_recipe_item(product)
            item = db.item_from_class_name(class_name)
            if item.is_liquid():
                amount = int(amount / 1000)
            self.__products[item.var()] = self.RecipeItem(
                item, amount, float(data["mManufactoringDuration"]))

    def slug(self):
        return self.__data["mDisplayName"].lower().replace(' ', '-').replace(':','')

    def var(self):
        return "recipe:" + self.slug()

    def viz_name(self):
        return "recipe-" + self.slug()

    def viz_label(self, amount):
        out = '<'
        out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        out += '<TR>'
        out += '<TD COLSPAN="3" BGCOLOR="lightgray">' + \
            str(round(amount, 2)) + 'x ' + \
            self.crafter().human_readable_name() + '</TD>'
        out += '</TR>'
        out += '<TR>'
        out += '<TD COLSPAN="3">' + self.human_readable_name() + '</TD>'
        out += '</TR>'

        def get_component_amount_label(component, recipe_amount):
            return str(round(amount * component.minute_rate(), 2)) + "/m "

        for ingredient in self.ingredients().values():
            out += '<TR>'
            out += '<TD BGCOLOR="moccasin">Input</TD>'
            out += '<TD>' + ingredient.item().human_readable_name() + '</TD>'
            out += '<TD>' + get_component_amount_label(ingredient, amount) + '</TD>'
            out += '</TR>'
        for product in self.products().values():
            out += '<TR>'
            out += '<TD BGCOLOR="lightblue">Output</TD>'
            out += '<TD>' + product.item().human_readable_name() + '</TD>'
            out += '<TD>' + get_component_amount_label(product, amount) + '</TD>'
            out += '</TR>'
        out += '</TABLE>>'
        return out

    def human_readable_name(self):
        return "Recipe: " + self.__data["mDisplayName"]

    def details(self):
        out = [self.human_readable_name()]
        out.append("  var: " + self.var())
        out.append("  time: " + str(float(self.__data["mManufactoringDuration"])) + "s")
        out.append("  crafted in: " + self.crafter().human_readable_name())
        out.append("  ingredients:")
        for ingredient in self.__ingredients.values():
            out.append("    " + ingredient.human_readable_name())
        out.append("  products:")
        for product in self.__products.values():
            out.append("    " + product.human_readable_name())
        out.append("")
        return '\n'.join(out)

    def embed(self):
        embed = Embed(title=self.human_readable_name())
        if self.is_alternate():
            embed.description = "**Alternate**"
        ingredients = "\n".join([ing.human_readable_name()
                                 for ing in self.ingredients().values()])
        embed.add_field(name="Ingredients", value=ingredients, inline=True)
        products = "\n".join([pro.human_readable_name()
                              for pro in self.products().values()])
        embed.add_field(name="Products", value=products, inline=True)
        embed.add_field(name="Crafting Time",
                        value=str(float(self.__data["mManufactoringDuration"])) + " seconds",
                        inline=True)
        embed.add_field(name="Building",
                        value=self.crafter().human_readable_name(),
                        inline=True)
        return embed

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
        return self.__data["mDisplayName"].startswith("Alternate: ")

    def is_craftable_in_building(self):
        return self.__crafter is not None
