import json
import re
import unicodedata
from pyparsing import Word, Optional, nums, oneOf, ParseException, Regex, Suppress, Combine


def normalize_text(text):
    text = unicodedata.normalize('NFKD', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_ingredient(ingredient):
    ingredient = normalize_text(ingredient)

    fraction = Combine(Word(nums) + '/' + Word(nums))
    mixed_num = Combine(Word(nums) + Optional(Suppress(' ') + fraction))
    quantity = (mixed_num | fraction | Word(
        nums + '.')).setResultsName('quantity')

    units_list = [
        'teaspoon', 'teaspoons', 'tsp',
        'tablespoon', 'tablespoons', 'tbsp',
        'cup', 'cups',
        'pint', 'pints',
        'quart', 'quarts',
        'gallon', 'gallons',
        'ounce', 'ounces', 'oz',
        'pound', 'pounds', 'lb', 'lbs',
        'gram', 'grams', 'g',
        'kilogram', 'kilograms', 'kg',
        'liter', 'liters', 'l',
        'milliliter', 'milliliters', 'ml',
        'package', 'packages',
        'can', 'cans',
        'slice', 'slices',
        'clove', 'cloves',
        'stick', 'sticks',
        'sprig', 'sprigs',
        'bunch', 'bunches',
        'pinch', 'pinches',
        'dash', 'dashes',
        'head', 'heads',
        'stalk', 'stalks',
        'piece', 'pieces',
        'medium', 'large', 'small',
        'jar', 'jars',
        'bottle', 'bottles',
        'bag', 'bags',
        'box', 'boxes',
        'block', 'blocks',
        'packet', 'packets',
        'envelope', 'envelopes',
        'sheet', 'sheets',
        'square', 'squares',
        'strip', 'strips',
        'drop', 'drops',
        'fillet', 'fillets',
        'inch', 'inches',
        # New units can be added here
    ]
    unit = oneOf(units_list).setResultsName('unit')

    # defining the ingredient name
    ingredient_name = Regex('.+').setResultsName('ingredient_name')

    # Defining the parser
    ingredient_parser = Optional(quantity) + Optional(unit) + ingredient_name

    try:
        parsed = ingredient_parser.parseString(ingredient)
        quantity_parsed = parsed.get('quantity', None)
        unit_parsed = parsed.get('unit', None)
        ingredient_name_parsed = parsed.get('ingredient_name', '').strip()

        quantity_value = None
        if quantity_parsed:
            quantity_str = quantity_parsed
            # Kesirli sayıları hesapla
            if ' ' in quantity_str:
                whole, frac = quantity_str.split(' ')
                num, denom = frac.split('/')
                quantity_value = float(whole) + float(num) / float(denom)
            elif '/' in quantity_str:
                num, denom = quantity_str.split('/')
                quantity_value = float(num) / float(denom)
            else:
                quantity_value = float(quantity_str)
        else:
            quantity_value = None

        return {
            'quantity': quantity_value,
            'unit': unit_parsed,
            'ingredient': ingredient_name_parsed
        }
    except ParseException:
        # If the ingredient cannot be parsed, return the original text
        return {
            'quantity': None,
            'unit': None,
            'ingredient': ingredient
        }


def extract_total_time(directions):
    total_minutes = 0
    for step in directions:
        step = normalize_text(step)
        matches = re.findall(r'(\d+)\s*(minutes?|hours?)',
                             step, flags=re.IGNORECASE)
        for amount, unit in matches:
            amount = int(amount)
            if 'hour' in unit.lower():
                amount *= 60
            total_minutes += amount
    if total_minutes > 0:
        return total_minutes
    else:
        return None


def process_recipes(data):
    recipes = []

    for recipe in data:
        title = recipe.get('title')
        if title:
            title = normalize_text(title)
            recipe_id = title
            name = title
        else:
            recipe_id = 'Unknown'
            name = 'Unknown'

        instructions_list = recipe.get('directions', [])

        instructions_list = [normalize_text(instr)
                             for instr in instructions_list]
        instructions = ' '.join(instructions_list).strip()

        calories = recipe.get('calories')
        fat = recipe.get('fat')
        protein = recipe.get('protein')
        sodium = recipe.get('sodium')
        rating = recipe.get('rating')
        desc = recipe.get('desc')

        if desc:
            desc = normalize_text(desc)
        else:
            desc = ''

        total_time = extract_total_time(instructions_list)

        ingredients = []
        for ingredient_text in recipe.get('ingredients', []):

            ingredient_text = normalize_text(ingredient_text)
            parsed = parse_ingredient(ingredient_text)
            quantity = parsed['quantity']
            unit = parsed['unit']
            ingredient_name = parsed['ingredient']

            ingredients.append({
                'name': ingredient_name,
                'quantity': quantity,
                'unit': unit
            })

        recipes.append({
            'recipe_id': recipe_id,
            'name': name,
            'instructions': instructions,
            'ingredients': ingredients,
            'total_time': total_time,
            'calories': calories,
            'fat': fat,
            'protein': protein,
            'sodium': sodium,
            'rating': rating,
            'desc': desc
        })

    return recipes


def main():
    # JSON verisini yükle
    with open('/Users/ilkeryasincakir/VsCodeProjects/GradProject/data/Epicurious/full_format_recipes.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Tarifleri işle
    recipes = process_recipes(data)

    # Sonuçları JSON olarak kaydet
    with open('recipes_output.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=4)

    print("İşlem tamamlandı. Sonuçlar 'recipes_output.json' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()
