from db import DB
from optimizer import Optimizer

class Satisfaction:
    def __init__(self):
        self.__db = DB("data.json")
        self.__opt = Optimizer(self.__db)

    def items(self, *args):
        print("calling !items with", len(args), "arguments:", ', '.join(args))

        if len(args) == 0:
            out = []
            for item in sorted(self.__db.items()):
                out.append(item)
            return '\n'.join(out)
        if len(args) == 1:
            item = args[0]
            if item not in self.__db.items():
                return "Unknown item: " + item
            return self.__db.items()[item].details()

    def recipes(self, *args):
        print("calling !recipes with", len(args), "arguments:", ', '.join(args))

        if len(args) == 0:
			out = []
			for recipe in sorted(self.__db.recipes()):
				out.append(recipe)
			return '\n'.join(out)
		if len(args) == 1:
			arg = args[0]
			if arg not in self.items and arg not in self.recipes:
				return "Unknown recipe or item: " + arg
			if arg in self.recipes:
				return self.get_recipe_details(arg)
			if arg in self.items:
				out = []
				out.append("Recipes producing item:")
				for recipe in self.recipes_for_product[arg]:
					out.append(self.get_recipe_details(recipe))
				out.append("Recipes requiring item:")
				for recipe in self.recipes_for_ingredient[arg]:
					out.append(self.get_recipe_details(recipe))
				return '\n'.join(out)

    def min(self, *args):
        print("calling !min with", len(args), "arguments:", ', '.join(args))

    def max(self, *args):
        print("calling !max with", len(args), "arguments:", ', '.join(args))