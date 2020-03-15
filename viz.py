

def get_recipe_viz_label(recipe, amount):
    out = '<'
    out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
    out += '<TR>'
    out += '<TD COLSPAN="2" BGCOLOR="lightgray">' +  str(round(amount, 2)) + 'x'
    out += '<BR/>' + recipe.human_readable_name() + '</TD>'
    out += '</TR>'
    for ingredient in recipe.ingredients().values():
        out += '<TR>'
        out += '<TD BGCOLOR="moccasin">Input</TD>'
        out += '<TD>' + ingredient.item().human_readable_name() + '</TD>'
        out += '</TR>'
    for product in recipe.products().values():
        out += '<TR>'
        out += '<TD BGCOLOR="lightblue">Output</TD>'
        out += '<TD>' + product.item().human_readable_name() + '</TD>'
        out += '</TR>'
    out += '</TABLE>>'
    return out

def get_input_viz_label(item_name, amount):
    out = '<'
    out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
    out += '<TR>'
    out += '<TD COLSPAN="2" BGCOLOR="moccasin">' +  str(round(amount, 2)) + '/m'
    out += '<BR/>' + item_name + '</TD>'
    out += '</TR>'
    out += '</TABLE>>'
    return out

def get_output_viz_label(item_name, amount):
    out = '<'
    out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
    out += '<TR>'
    out += '<TD COLSPAN="2" BGCOLOR="lightblue">' +  str(round(amount, 2)) + '/m'
    out += '<BR/>' + item_name + '</TD>'
    out += '</TR>'
    out += '</TABLE>>'
    return out

def get_edge_label(item, amount):
    return str(round(amount, 2)) + '/m\n' +  item

def get_power_recipe_node_name(fuel_item):
    return "power-recipe-" + fuel_item.var()

def get_power_recipe_label(power_recipe, amount):
    out = '<'
    out += '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
    out += '<TR>'
    out += '<TD COLSPAN="2" BGCOLOR="lightgray">' +  str(round(amount, 2)) + 'x'
    out += '<BR/>' + power_recipe.generator().human_readable_name() + '</TD>'
    out += '</TR>'
    out += '<TR>'
    out += '<TD BGCOLOR="moccasin">Input</TD>'
    out += '<TD>' + power_recipe.fuel_item().human_readable_name() + '</TD>'
    out += '</TR>'
    out += '</TABLE>>'
    return out
