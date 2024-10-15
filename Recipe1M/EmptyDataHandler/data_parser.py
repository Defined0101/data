import pandas as pd
import bisect
import re
import numpy as np
import ast
import unicodedata
import os
from fractions import Fraction
import json
from joblib import Parallel, delayed  # For parallel processing

calorie_lookup = {}

def parse_fraction(fraction_str):
    """
    Convert a fraction or mixed fraction string to a float. Handle cases like "1/2" or "5 1/2".
    """
    try:
        if isinstance(fraction_str, (float, int)):
            return float(fraction_str)

        if ' ' in fraction_str:  # Handle mixed fractions like "5 1/2"
            whole_number, fraction_part = fraction_str.split()
            return float(int(whole_number) + Fraction(fraction_part))
        return float(Fraction(fraction_str))  # Handle simple fractions like "1/2"
    
    except (ValueError, TypeError):
        return None  # Return None if input is invalid

def normalize_text(text):
    """
    Normalize text by removing special characters and excessive spaces.
    """
    text = unicodedata.normalize('NFKD', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_total_time(directions):
    """
    Extract the total time from the recipe instructions (in minutes).
    """
    total_minutes = 0
    for step in directions:
        step = normalize_text(step)
        # Find all occurrences of time units (minutes/hours) in the step
        matches = re.findall(r'(\d+)\s*(minutes?|hours?)', step, flags=re.IGNORECASE)
        
        for amount, unit in matches:
            amount = int(amount)
            if 'hour' in unit.lower():
                amount *= 60  # Convert hours to minutes
            total_minutes += amount

    return total_minutes if total_minutes > 0 else None

# Pattern to match quantity, unit, and ingredient in the ingredient text
quantity_unit_pattern = r"(?P<quantity>[\d/\.\s]+)\s*(?P<unit>[a-zA-Z\.]+)?\s*(?P<ingredient>.*)"
# Pattern to remove unnecessary text in parentheses
cleanup_pattern = r"\(.*?\)"
# Pattern to handle numeric ranges, e.g., "1/4 to 1/2"
numeric_range_pattern = r"\b(\d+/\d+|\d+(\.\d+)?)\s*to\s*(\d+/\d+|\d+(\.\d+)?)\b"
# Pattern to convert plural forms to singular
plural_pattern = r"\b([a-zA-Z]+)s\b"

# Dictionary to convert unit abbreviations to full names
unit_expansions = {
    "tbsp": "tablespoon",
    "tsp": "teaspoon",
    "oz": "ounce",
    "fluid ounce": "fl. oz",
    "lb": "pound",
    "gram": "g",
    "kilogram": "kg",
    "l": "liter",
    "milliliter": "ml",
    "c": "cup",
    "leaves": "leaf"
}

# List of known units
known_units = [
    "bushel", "cup", "dash", "drop", "fl. oz", "g", "gallon", "glass", "kg", "liter", "ml", "ounce", "pinch", "pint", "pound", "quart", "scoop", "shot", "tablespoon", "teaspoon", "leaf"
]

def expand_unit(unit):
    """
    Convert unit abbreviations to full names.
    """
    return unit_expansions.get(unit, unit)

def parse_ingredient(ingredient_text):
    """
    Parse an ingredient string to extract quantity, unit, and ingredient name.
    """
    # Remove unnecessary parenthetical information
    cleaned_text = re.sub(cleanup_pattern, "", ingredient_text).strip()
    # Handle numeric ranges by taking the lower bound
    cleaned_text = re.sub(numeric_range_pattern, lambda m: m.group(1), cleaned_text).strip()
    match = re.match(quantity_unit_pattern, cleaned_text)
    if match:
        quantity = match.group('quantity').strip() if match.group('quantity') else ''
        unit = match.group('unit').replace('.', '').strip() if match.group('unit') else ''  # Remove periods from unit
        # Expand units to their full names
        unit = expand_unit(unit)
        # Convert plural units to singular
        unit = re.sub(plural_pattern, r"\1", unit).strip()
        ingredient = match.group('ingredient').strip() if match.group('ingredient') else ''
        # Clean up ingredient alternatives and remove numerical references
        ingredient = re.sub(r"\b\d+(/\d+)?\b", "", ingredient).strip()  # Remove numeric references
        ingredient = re.sub(r",.*", "", ingredient).strip()  # Remove text after commas
        ingredient = re.sub(r" or ", "/", ingredient)  # Replace "or" with "/" to handle alternatives
        if unit:
            ingredient = re.sub(rf"\b{unit}\b", "", ingredient).strip()  # Remove the unit from ingredient name
        ingredient = re.sub(plural_pattern, r"\1", ingredient).strip()  # Convert plurals to singular
        if not ingredient and unit:
            return quantity, 'piece', unit
        if not ingredient:
            return None, None, None
        if unit in known_units:
            return quantity, unit, ingredient
        else:
            return quantity, 'piece', f'{unit.lower()} {ingredient.lower()}'
    return None, None, ingredient_text

def get_nutr(ingredient, unit, quantity=1):
    """
    Get nutritional information (calories, protein, fat, sugar) for a given ingredient.
    """
    try:
        # Find matching ingredient if exact match is not found
        matching_ingredients = [key for key in calorie_lookup if ingredient.lower() in key.lower()]
        if not matching_ingredients:
            return [0, 0, 0, 0]
        matched_ingredient = matching_ingredients[0]
        return np.array(calorie_lookup[matched_ingredient][unit]) * float(quantity)
    except Exception as e:
        return [0, 0, 0, 0]

# Initialize lists to store calculated data
total_time_list = []
calories_list = []
protein_list = []
fat_list = []
sugar_list = []
ingredients_list = []
ing_cal_list = []

def process_apply(row):
    """
    Process a single row to extract total time, nutrients, and ingredients, and store them in lists.
    """
    index = row.name

    # Parse ingredients, units, and nutrition data
    instructions = ast.literal_eval(row['Instructions'])
    ingredients = ast.literal_eval(row['Ingredients'])

    total_calories = total_protein = total_fat = total_sugar = 0
    parsed_ingredients = []
    for ingredient in ingredients:
        quantity, unit, ingredient_name = parse_ingredient(ingredient)
        numbered_quantity = parse_fraction(quantity)
        parsed_ingredients.append({
            "name": ingredient_name,
            "unit": unit,
            "quantity": round(numbered_quantity, 2) if numbered_quantity else None
        })
        cal, pro, fat, sug = get_nutr(ingredient_name, unit, round(numbered_quantity, 2) if numbered_quantity else None)
        total_calories += cal if cal else 0
        total_protein += pro if pro else 0
        total_fat += fat if fat else 0
        total_sugar += sug if sug else 0

    # Extract total time from instructions
    total_time_list[index] = extract_total_time(instructions)

    # Replace double quotes in recipe name
    row['Name'].replace('"', '')

    row['Instructions'] = instructions

    # Append calculated values to respective lists
    calories_list[index] = round(total_calories, 2) if total_calories != 0 else 0
    protein_list[index] = round(total_protein, 2) if total_protein != 0 else 0
    fat_list[index] = round(total_fat, 2) if total_fat != 0 else 0
    sugar_list[index] = round(total_sugar, 2) if total_sugar != 0 else 0
    ingredients_list[index] = parsed_ingredients

def process_data(df):
    """
    Process the entire DataFrame by applying row-wise transformations.
    """
    length = df.shape[0]

    # Clear global lists before starting
    global total_time_list, calories_list, protein_list, fat_list, sugar_list, ingredients_list, unit_calorie_list
    total_time_list = np.empty((length,), dtype=object)
    calories_list = np.empty((length,), dtype=float)
    protein_list = np.empty((length,), dtype=float)
    fat_list = np.empty((length,), dtype=float)
    sugar_list = np.empty((length,), dtype=float)
    ingredients_list = np.empty((length,), dtype=object)
    desc_list = [''] * length

    # Apply the process_apply function to each row
    df.apply(process_apply, axis=1)

    # Add the lists as new columns to the DataFrame
    df['total_time'] = total_time_list
    df['calories'] = calories_list
    df['protein'] = protein_list
    df['fat'] = fat_list
    df['sugar'] = sugar_list
    df['ingredients'] = ingredients_list
    df['desc'] = desc_list

    # Drop unnecessary columns and return the processed DataFrame
    return df.drop(['Ingredients'], axis=1)

def parser_main():
    """
    Main function to process all recipe data files and save the results in smaller batches.
    """
    path_of_the_current_scripts_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir_path = os.path.join(path_of_the_current_scripts_dir, "../empty_partitioned_data")
    data_out_path = os.path.join(path_of_the_current_scripts_dir, "../processed_data")
    
    os.makedirs(data_out_path, exist_ok=True)

    global ing_cal_list

    # Load the calorie lookup table from a JSON file
    with open(os.path.join(path_of_the_current_scripts_dir, '../processed_data', 'ingredients_calories_table.json'), 'r') as ing_cal_json:
        ing_cal_list = json.load(ing_cal_json)
    
    # Populate the calorie lookup dictionary
    for entry in ing_cal_list:
        ingredient, unit, calories, protein, fat, sugar = entry.split("|")
        if ingredient not in calorie_lookup:
            calorie_lookup[ingredient] = {}
        calorie_lookup[ingredient][unit] = [
            float(calories),
            float(protein),
            float(fat),
            float(sugar),
        ]

    # Process files in batches of 8
    all_files = os.listdir(data_dir_path)
    batch_size = 8
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i + batch_size]
        df_list = []

        # Use Parallel to process files concurrently within each batch
        df_list = Parallel(n_jobs=-1)(
            delayed(lambda file: process_data(pd.read_csv(os.path.join(data_dir_path, file))))(file)
            for file in batch_files
        )

        # Concatenate DataFrames of the current batch and save as a separate file
        if df_list:
            batch_df = pd.concat(df_list, ignore_index=True)

            # Save final DataFrame as JSON
            with open(os.path.join(data_out_path, f'processed_batch_{i // batch_size + 1}.json'), 'w') as json_file:
                json.dump(batch_df.to_dict(orient='records'), json_file, indent=4)

            # Save final DataFrame as a Parquet file
            output_file_path = os.path.join(data_out_path, f'processed_batch_{i // batch_size + 1}.parquet')
            batch_df.to_parquet(output_file_path, index=False, engine='pyarrow')

# Execute the main function when the script is run
if __name__ == "__main__":
    import time
    start_time = time.time()
    parser_main()
    print(f"Processing completed in {time.time() - start_time:.2f} seconds")
