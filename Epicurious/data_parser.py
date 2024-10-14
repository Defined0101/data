import json
import re
import unicodedata
from pyparsing import (
    Word, Optional, nums, oneOf, ParseException, Suppress, Combine, White, restOfLine
)


def normalize_text(text):
    text = unicodedata.normalize('NFKD', text)
    fractions = {
        '½': '1/2',
        '⅓': '1/3',
        '⅔': '2/3',
        '¼': '1/4',
        '¾': '3/4',
        '⅛': '1/8',
        '⅜': '3/8',
        '⅝': '5/8',
        '⅞': '7/8',
    }
    for unicode_frac, replacement in fractions.items():
        text = text.replace(unicode_frac, replacement)

    text = text.replace('⁄', '/')
    text = re.sub(r'\s+', ' ', text)
    # remove small, medium, large
    text = re.sub(r'\b(?:small|medium|large)\b', '', text, flags=re.IGNORECASE)
    return text.strip()


def parse_ingredient(ingredient):
    ingredient = normalize_text(ingredient)

    fraction = Combine(Word(nums) + '/' + Word(nums))
    mixed_num = Combine(Word(nums) + Suppress(White()) + fraction)

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
    ]

    unit = oneOf(units_list, caseless=True,
                 asKeyword=True).setResultsName('unit')

    ingredient_name = restOfLine.setResultsName('ingredient_name')

    with_quantity_unit = (
        quantity + unit + Suppress(White()) + ingredient_name)

    with_quantity_only = (quantity + Suppress(White()) + ingredient_name)

    without_quantity_unit = ingredient_name

    ingredient_parser = with_quantity_unit | with_quantity_only | without_quantity_unit

    try:
        parsed = ingredient_parser.parseString(ingredient)

        quantity_value = None
        unit_parsed = None
        ingredient_name_parsed = ''

        if 'unit' in parsed:

            quantity_parsed = parsed.get('quantity', None)
            unit_parsed = parsed.get('unit', None)
            ingredient_name_parsed = parsed.get('ingredient_name', '').strip()
        elif 'quantity' in parsed:
            quantity_parsed = parsed.get('quantity', None)
            ingredient_name_parsed = parsed.get('ingredient_name', '').strip()
        else:
            ingredient_name_parsed = parsed.get('ingredient_name', '').strip()

        if 'quantity_parsed' in locals() and quantity_parsed:
            quantity_str = quantity_parsed
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
            'unit': unit_parsed.lower() if unit_parsed else None,
            'ingredient': ingredient_name_parsed
        }
    except ParseException as pe:
        print(f"ParseException: {pe} for ingredient: {ingredient}")
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
        return int(total_minutes)
    else:
        return None


def process_recipes(data):
    recipes = []

    for recipe in data:
        title = recipe.get('title')
        if title:
            title = normalize_text(title)
            name = title
        else:
            name = 'Unknown'

        instructions_list = recipe.get('directions', [])

        instructions_list = [normalize_text(instr)
                             for instr in instructions_list]
        instructions = ' '.join(instructions_list).strip()

        calories = recipe.get('calories')
        fat = recipe.get('fat')
        protein = recipe.get('protein')
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
            'name': name,
            'instructions': instructions,
            'ingredients': ingredients,
            'total_time': total_time,
            'calories': calories,
            'fat': fat,
            'protein': protein,
            'desc': desc
        })

    return recipes


def main():

    with open('/Users/ilkeryasincakir/VsCodeProjects/GradProject/data/Epicurious/full_format_recipes.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    recipes = process_recipes(data)
    with open('Epicurious/recipes_output.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=4)

    print("İşlem tamamlandı. Sonuçlar 'recipes_output.json' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()
