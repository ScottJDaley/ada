from ada.query import OptimizationQuery
from ada.result import RecipeCompareResult

class RecipeComparer:
    class RecipeStats:
        def __init__(self, recipe, product, recipe_blacklist, opt):
            # run the query
            self.__recipe = recipe
            self.__opt = opt

            self.__query = OptimizationQuery("")
            self.__query.maximize_objective = False
            self.__query.objective_coefficients = {"unweighted-resources": -1} 
            self.__query.eq_constraints[product.var()] = 1
            for blacklisted in recipe_blacklist:
                self.__query.eq_constraints[blacklisted.var()] = 0
        
        def recipe(self):
            return self.__recipe

        async def compute(self):
            result = await self.__opt.optimize(self.__query)
            print(result)


    def __init__(self, db, opt):
        self.__db = db
        self.__opt = opt

    async def compare(self, query):
        print("called compare() with query: '" + str(query) + "'")

        for product in query.base_recipe.products().values():
            print("Found product: " + product.item().human_readable_name())
            related_recipes = []
            for related_recipe in self.__db.recipes_for_product(product.item().var()):
                if related_recipe ==  query.base_recipe:
                    continue
                print("Found related recipe: " + related_recipe.human_readable_name())
                print("Found related recipe var: " + related_recipe.var())
                related_recipes.append(related_recipe)
            
            base_stats = self.RecipeStats(query.base_recipe, product.item(), related_recipes, self.__opt)
            await base_stats.compute()

            continue; # TODO: Not yet supporting multiple products.

        # For the base and each related recipe we want to run an optimization query to produce
        # one of the product. We also need to disable all related recipes to force this candidate
        # to be used. 

        # The goal is to get, for each candidate recipe, the ingredients, any other products,
        # the raw resources, total power, physical space required, number of steps, etc.


        return RecipeCompareResult("compare result")