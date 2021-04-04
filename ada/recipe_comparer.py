from typing import NamedTuple
from ada.query import OptimizationQuery
from ada.result import RecipeCompareResult


class RecipeComparer:
    class ProductionStats(NamedTuple):
        power_consumption: float
        inputs: dict
        step_count: int

    class RecipeStatsOld:
        def __init__(self, recipe, opt):
            # run the query
            self.__recipe = recipe
            self.__opt = opt

            # self.__query = OptimizationQuery("")
            # self.__query.maximize_objective = False
            # self.__query.objective_coefficients = {"unweighted-resources": -1}
            # self.__query.eq_constraints[product.var()] = 1
            # for blacklisted in recipe_blacklist:
            #     self.__query.eq_constraints[blacklisted.var()] = 0

        def recipe(self):
            return self.__recipe

        def default_power_consumption(self):
            return -self.__default_result.net_power() + self.__recipe.crafter().power_consumption()

        def optimal_power_consumption(self):
            return -self.__optimal_result.net_power() + self.__recipe.crafter().power_consumption()

        def default_raw_inputs(self):
            return self.__default_result.inputs()

        def optimal_raw_inputs(self):
            return self.__optimal_result.inputs()

        def default_step_count(self):
            return len(self.__default_result.recipes()) + len(self.default_raw_inputs()) + 1

        def optimal_step_count(self):
            return len(self.__optimal_result.recipes()) + len(self.optimal_raw_inputs()) + 1

        async def compute(self):
            # We first want to figure out how much of the ingredients we need to produce
            # 1 of the products using this recipe.

            # We should also keep track of any other products and the power required for
            # this recipe.

            # First, how many of the desired product does this recipe produce?
            # product_amount = 0
            # other_product_amounts = {}
            # for product_var, product in self.__recipe.products().items():
            #     if product_var == self.__product.var():
            #         product_amount = product.amount()
            #     else:
            #         other_product_amounts[product_var] = product.amount()

            query = OptimizationQuery("")
            query.maximize_objective = False
            query.objective_coefficients = {"unweighted-resources": -1}
            for ingredient_var, ingredient in self.__recipe.ingredients().items():
                query.eq_constraints[ingredient_var] = ingredient.minute_rate()

            self.__optimal_result = await self.__opt.optimize(query)

            # Run again, this time disallowing alternate recipes.
            query.eq_constraints["alternate-recipes"] = 0
            self.__default_result = await self.__opt.optimize(query)

            print(self.__optimal_result)

    def __init__(self, db, opt):
        self.__db = db
        self.__opt = opt

    async def compute_recipe_stats(self, recipe, exclude_alternate_recipes):
        query = OptimizationQuery("")
        query.maximize_objective = False
        query.objective_coefficients = {"unweighted-resources": -1}
        for ingredient_var, ingredient in recipe.ingredients().items():
            query.eq_constraints[ingredient_var] = ingredient.minute_rate()

        # optimal_result = await self.__opt.optimize(query)

        # Run again, this time disallowing alternate recipes.
        if exclude_alternate_recipes:
            query.eq_constraints["alternate-recipes"] = 0

        result = await self.__opt.optimize(query)

        print(optimal_result)

        default_stats = ProductionStats(
            "power_consumption", -result.net_power() +
            recipe.crafter().power_consumption(),
            "inputs", result.inputs(),
            "step_count", len(result.recipes()) +
            len(result.inputs()) + 1
        )

    async def compare(self, query):
        print("called compare() with query: '" + str(query) + "'")

        base_stats = self.RecipeStatsOld(query.base_recipe, self.__opt)
        await base_stats.compute()

        print("=== Overall Stats ===")

        print("\nINPUTS:")
        print("Base:")
        for ingredient in query.base_recipe.ingredients().values():
            print(" ", ingredient.item().human_readable_name() +
                  ":", ingredient.minute_rate(), "/m")
        print("From raw (optimal productivity without alternate recipes):")
        for (_input, value) in base_stats.default_raw_inputs().values():
            print(" ", _input.human_readable_name() + ":", value, "/m")
        print("From raw (optimal productivity with alternate recipes):")
        for (_input, value) in base_stats.optimal_raw_inputs().values():
            print(" ", _input.human_readable_name() + ":", value, "/m")

        print("\nPOWER CONSUMPTION:")
        print("Base:", query.base_recipe.crafter().power_consumption(), "MW")
        print("From raw (optimal productivity without alternate recipes):",
              base_stats.default_power_consumption(), "MW")
        print("From raw (optimal productivity with alternate recipes):",
              base_stats.optimal_power_consumption(), "MW")

        print("\nPROCESSING STEPS:")
        print("From raw (optimal productivity without alternate recipes):",
              base_stats.default_step_count())
        print("From raw (optimal productivity with alternate recipes):",
              base_stats.optimal_step_count())

        print("\n")

        for product in query.base_recipe.products().values():
            print("=== Evaluating for",
                  product.item().human_readable_name(), "product ===")

            product_minute_rate = product.minute_rate()

            print("\nINPUTS:")
            print("Base:")
            for ingredient in query.base_recipe.ingredients().values():
                print(" ", ingredient.item().human_readable_name() +
                      ":", ingredient.minute_rate() / product_minute_rate)
            print("From raw (optimal productivity without alternate recipes):")
            for (_input, value) in base_stats.default_raw_inputs().values():
                print(" ", _input.human_readable_name() +
                      ":", value / product_minute_rate)
            print("From raw (optimal productivity with alternate recipes):")
            for (_input, value) in base_stats.optimal_raw_inputs().values():
                print(" ", _input.human_readable_name() +
                      ":", value / product_minute_rate)

            print("\nPOWER CONSUMPTION:")
            print("Base:", query.base_recipe.crafter(
            ).power_consumption() / product_minute_rate, "MW")
            print("From raw (optimal productivity without alternate recipes):",
                  base_stats.default_power_consumption() / product_minute_rate, "MW")
            print("From raw (optimal productivity with alternate recipes):",
                  base_stats.optimal_power_consumption() / product_minute_rate, "MW")

            print("\nPROCESSING STEPS:")
            print("From raw (optimal productivity without alternate recipes):",
                  base_stats.default_step_count())
            print("From raw (optimal productivity with alternate recipes):",
                  base_stats.optimal_step_count())

            print("\n")

            related_recipes = []
            for related_recipe in self.__db.recipes_for_product(product.item().var()):
                if related_recipe.var() == query.base_recipe.var():
                    continue
                print("Found related recipe: " +
                      related_recipe.human_readable_name())
                related_recipes.append(related_recipe)

                related_stats = self.RecipeStatsOld(related_recipe, self.__opt)
                await related_stats.compute()

                related_product_minute_rate = 1
                for related_product in related_recipe.products().values():
                    if related_product.item().var() == product.item().var():
                        related_product_minute_rate = related_product.minute_rate()

                print("\nINPUTS:")
                print("Base:")
                for ingredient in related_recipe.ingredients().values():
                    print(" ", ingredient.item().human_readable_name() +
                          ":", ingredient.minute_rate() / related_product_minute_rate)
                print("From raw (optimal productivity without alternate recipes):")
                for (_input, value) in related_stats.default_raw_inputs().values():
                    print(" ", _input.human_readable_name() +
                          ":", value / related_product_minute_rate)
                print("From raw (optimal productivity with alternate recipes):")
                for (_input, value) in related_stats.optimal_raw_inputs().values():
                    print(" ", _input.human_readable_name() +
                          ":", value / related_product_minute_rate)

                print("\nPOWER CONSUMPTION:")
                print("Base:", related_recipe.crafter(
                ).power_consumption() / related_product_minute_rate, "MW")
                print("From raw (optimal productivity without alternate recipes):",
                      related_stats.default_power_consumption() / related_product_minute_rate, "MW")
                print("From raw (optimal productivity with alternate recipes):",
                      related_stats.optimal_power_consumption() / related_product_minute_rate, "MW")

                print("\nPROCESSING STEPS:")
                print("From raw (optimal productivity without alternate recipes):",
                      related_stats.default_step_count())
                print("From raw (optimal productivity with alternate recipes):",
                      related_stats.optimal_step_count())

                print("\n")

        #     base_stats = self.RecipeStats(query.base_recipe, self.__opt)
        #     await base_stats.compute()

        #     continue  # TODO: Not yet supporting multiple products.

        # For the base and each related recipe we want to run an optimization query to produce
        # one of the product. We also need to disable all related recipes to force this candidate
        # to be used.

        # The goal is to get, for each candidate recipe, the ingredients, any other products,
        # the raw resources, total power, physical space required, number of steps, etc.

        return RecipeCompareResult("compare result")
