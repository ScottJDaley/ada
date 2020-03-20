import re

class ParseException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class QueryParser:
    def __init__(self, variables):
        self.__variables = variables

        unweighted_resources = {
            "resource:water:input": 0,
            "resource:iron-ore:input": 1,
            "resource:copper-ore:input": 1,
            "resource:limestone:input": 1,
            "resource:coal:input": 1,
            "resource:crude-oil:input": 1,
            "resource:bauxite:input": 1,
            "resource:caterium-ore:input": 1,
            "resource:uranium:input": 1,
            "resource:raw-quartz:input": 1,
            "resource:sulfur:input": 1,
        }
        # Proportional to amount of resource on map
        weighted_resources = {
            "resource:water:input": 0,
            "resource:iron-ore:input": 1,
            "resource:copper-ore:input": 3.29,
            "resource:limestone:input": 1.47,
            "resource:coal:input": 2.95,
            "resource:crude-oil:input": 4.31,
            "resource:bauxite:input": 8.48,
            "resource:caterium-ore:input": 6.36,
            "resource:uranium:input": 46.67,
            "resource:raw-quartz:input": 6.36,
            "resource:sulfur:input": 13.33,
        }
        # Square root of weighted amounts above
        mean_weighted_resources = {
            "resource:water:input": 0,
            "resource:iron-ore:input": 1,
            "resource:copper-ore:input": 1.81,
            "resource:limestone:input": 1.21,
            "resource:coal:input": 1.72,
            "resource:crude-oil:input": 2.08,
            "resource:bauxite:input": 2.91,
            "resource:caterium-ore:input": 2.52,
            "resource:uranium:input": 6.83,
            "resource:raw-quartz:input": 2.52,
            "resource:sulfur:input": 3.65,
        }
        self.__built_in_objectives = {
            "unweighted-resources": unweighted_resources,
            "weighted-resources": weighted_resources,
            "mean-weighted-resources": mean_weighted_resources,
        }

    def partition_variables_by_match_order(self):
        match_groups = [
            '^power$',
            '^resource:.*:input$',
            '^resource:.*:output$',
            '^item:.*:output$',
            '^item:.*:input$',
            '^.*$',
        ]
        def matches_for(group):
            return [var for var in self.__variables if re.match(group, var)]
        return [matches_for(group) for group in match_groups]

    async def pick_variable(self, request_input_fn, var_expr, vars):
        out = []
        out.append("Input '" + var_expr + "' matches multiple variables, pick one:")
        for i, var in enumerate(vars, start=1):
            out.append("  " + str(i) + ") " + var)
        num_choices = len(vars) +1
        out.append("  " + str(num_choices) + ") apply expression to all matches")
        out.append("Enter a number between 1 and " + str(num_choices))
        attempts = 0
        while attempts < 3:
            attempts += 1
            choice = await request_input_fn('\n'.join(out))
            if not choice.isdigit():
                continue
            index = int(choice)
            if index <= 0 or index > num_choices:
                continue
            if index <= len(vars):
                return [vars[index - 1]]
            return vars
        raise ParseException("Could not parse input '" + var_expr + "'")

    async def parse_variables(self, request_input_fn, var_expr):
        for partition in self.partition_variables_by_match_order():
            inner_matched = [var for var in partition if var_expr in var.split(':')]
            substring_matched = [var for var in partition if var_expr in var]
            re_matched = [var for var in partition if re.search(var_expr, var)]
            if len(inner_matched) == 1:
                return inner_matched
            if len(inner_matched) > 1:
                return await self.pick_variable(request_input_fn, var_expr, inner_matched)
            if len(substring_matched) == 1:
                return substring_matched
            if len(substring_matched) > 1:
                return await self.pick_variable(request_input_fn, var_expr, substring_matched)
            if len(re_matched) > 0:
                return re_matched
        raise ParseException("Input '" + var_expr + "' does not match any variables")

    async def parse_constraints(self, request_input_fn, *args):
        # First separate constraints by 'and'
        constraints_raw = []
        start_index = 0
        index = 0
        while index <= len(args):
            if index >= len(args) or args[index] == "and":
                constraints_raw.append(args[start_index:index])
                start_index = index + 1
            index += 1

        # Then parse the constraints
        #     var => (op, bound)
        constraints = {}
        for constraint in constraints_raw:
            if len(constraint) != 3:
                raise ParseException(
                    "Constraint must be in the form {{item}} {{=|<=|>=}} {{number}}.")
            expanded_vars = await self.parse_variables(request_input_fn, constraint[0])
            operator = constraint[1]
            try:
                bound = int(constraint[2])
            except ValueError:
                raise ParseException("Constraint bound must be an number.")
            if operator != "=" and operator != ">=" and operator != "<=":
                raise ParseException("Constraint operator must be one of {{=|<=|>=}}")
            for var in expanded_vars:
                constraints[var] = (operator, bound)
        return constraints

    async def parse_objective(self, request_input_fn, *args):
        # TODO: Support expression objectives
        if len(args) > 1:
            raise ParseException(
                "Input must be in the form {{item}} where {{item}} {{=|<=|>=}} {{number}} ")
        arg0 = args[0]
        objective = {}
        objective_vars = []
        if arg0 in self.__built_in_objectives:
            for var_name, coefficient in self.__built_in_objectives[arg0].items():
                objective[self.__variables[var_name]] = coefficient
                objective_vars.append(var_name)
        else:
            objective_items = await self.parse_variables(request_input_fn, arg0)
            for objective_item in objective_items:
                objective[self.__variables[objective_item]] = 1
                objective_vars.append(objective_item)
        return objective, objective_vars

    async def parse_input(self, request_input_fn, *args):
        # First separate out the {item} where clause
        if len(args) < 2:
            raise ParseException(
                "Input must be in the form {{item}} where {{item}} {{=|<=|>=}} {{number}} ")
        where_index = -1
        for i in range(len(args)):
            arg = args[i]
            if arg == "where":
                where_index = i
        if where_index <= 0:
            objective, objective_vars = await self.parse_objective(request_input_fn, "weighted-resources")
        else:
            objective, objective_vars = await self.parse_objective(request_input_fn, *args[:where_index])
        constraints = await self.parse_constraints(request_input_fn, *args[where_index+1:])
        query_vars = objective_vars
        for var in constraints:
            query_vars.append(var)
        return objective, constraints, query_vars

