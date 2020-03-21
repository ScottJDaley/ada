import json

with open("Docs.json") as f:
    raw = json.load(f)

with open('raw.json', 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False, indent=4)

for entry in raw:
    print(entry["NativeClass"])



for entry in raw:
    if entry["NativeClass"] == "Class'/Script/FactoryGame.FGItemDescriptor'":
        print(entry["Classes"])

data = {}
for entry in raw:
    data[entry["NativeClass"]] = entry["Classes"]

# We want the following:
# - items
# - resources
# - buildings (crafters, generators, miners)
# - recipes
item_classes = ['FGItemDescriptor']
resource_classes = ['FGResourceDescriptor']
crafter_classes = ['FGBuildableManufacturer']
generator_classes = ['FGBuildableGeneratorFuel',
                     'FGBuildableGeneratorNuclear',
                     'FGBuildableGeneratorGeoThermal']
recipe_classes = ['FGRecipe']

with open('new_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

