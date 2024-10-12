import pandas as pd
import bisect
import re
import numpy as np
import ast
import unicodedata
import os
from fractions import Fraction
import json

# Initialize global lists and sets
sorted_ing_list = []
sorted_unit_list = []
unique_ing_set = set()  # To track unique ingredient entries for quick lookup
unique_unit_set = set()  # To track unique units for quick lookup

def append_sorted(ing, unit, calories):
    """
    Insert the ingredient element into sorted_ing_list and sorted_unit_list in a sorted manner using binary search.
    """
    element = f'{ing}|{unit}|{calories}'
    comparing_element = f'{ing}|{unit}'

    # Use the set to check for uniqueness first
    if comparing_element not in unique_ing_set:
        # Use binary search to find the insertion point
        index_ing = bisect.bisect_left(sorted_ing_list, comparing_element)
        
        # Append the ingredient if it's not already in the sorted list
        sorted_ing_list.insert(index_ing, element)
        unique_ing_set.add(comparing_element)  # Add to the set to ensure uniqueness
    
    # Append the unit if it's not already in the sorted list
    if unit not in unique_unit_set:
        index_unit = bisect.bisect_left(sorted_unit_list, unit)
        sorted_unit_list.insert(index_unit, unit)
        unique_unit_set.add(unit)  # Add to the set to ensure uniqueness

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
        matches = re.findall(r'(\d+)\s*(minutes?|hours?)', step, flags=re.IGNORECASE)
        
        for amount, unit in matches:
            amount = int(amount)
            if 'hour' in unit.lower():
                amount *= 60  # Convert hours to minutes
            total_minutes += amount

    return total_minutes if total_minutes > 0 else None

def ing_parser(ingredients, units, quantities, nutr_info):
    """
    Parse ingredients, units, and quantities from a row, and calculate calories per unit.
    """
    for index, ing in enumerate(ingredients):
        ing = ing.split(', ')[0]  # Extract the main ingredient name
        unit = units[index]
        quantity = parse_fraction(quantities[index])
        
        if quantity is None or quantity == 0:
            continue  # Skip invalid or zero quantities
        
        # Calculate calories per unit
        calories_of_ing = float(nutr_info[index]['nrg'])
        unit_calories = calories_of_ing / quantity if quantity else 0
        
        # Append to the sorted ingredient and unit lists
        append_sorted(ing, unit, '{:.2f}'.format(unit_calories))

def create_ingredient_element(ingredients, units, quantities):
    """
    Create a structured list of ingredients with units and quantities for a recipe row.
    """
    return [{'name': ingredient, 'unit': unit, 'quantity': quantity}
                      for ingredient, unit, quantity in zip(ingredients, units, quantities)]

# Initialize lists to store calculated data
total_time_list = []
calories_list = []
protein_list = []
fat_list = []
sugar_list = []
ingredients_list = []

def process_apply(row):
    """
    Process a single row to extract total time, nutrients, and ingredients, and store them in lists.
    """
    index = row.name

    # Parse ingredients, units, and nutrition data only once
    instructions = ast.literal_eval(row['Instructions'])
    ingredients = ast.literal_eval(row['Ingredients'])
    units = ast.literal_eval(row['unit'])
    quantities = ast.literal_eval(row['quantity'])
    nutr_info = ast.literal_eval(row['nutr_per_ingredient'])

    # Extract total time from instructions
    total_time_list[index] = extract_total_time(instructions)

    # Replace double quotes in recipe name
    row['Name'].replace('"', '')

    row['Instructions'] = instructions

    # Parse and process ingredients
    ing_parser(ingredients, units, quantities, nutr_info)

    # Sum up nutrient values from `nutr_per_ingredient`
    total_calories = total_protein = total_fat = total_sugar = 0

    for nutr in nutr_info:
        total_calories += nutr['nrg']
        total_protein += nutr['pro']
        total_fat += nutr['fat']
        total_sugar += nutr['sug']

    # Append calculated values to respective lists
    calories_list[index] = round(total_calories, 2)
    protein_list[index] = round(total_protein, 2)
    fat_list[index] = round(total_fat, 2)
    sugar_list[index] = round(total_sugar, 2)
    ingredients_list[index] = create_ingredient_element(ingredients, units, quantities)

def process_data(df):
    """
    Process the entire DataFrame by applying row-wise transformations.
    """
    length = df.shape[0]

    # Clear global lists before starting
    global total_time_list, calories_list, protein_list, fat_list, sugar_list, ingredients_list
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
    df['Sugar'] = sugar_list
    df['ingredients'] = ingredients_list
    df['desc'] = desc_list

    # Drop unnecessary columns and return the processed DataFrame
    return df.drop(['nutr_values_per100g', 'fsa_lights_per100g', 'weight_per_ingr',
                    'Ingredients', 'unit', 'quantity', 'nutr_per_ingredient'], axis=1)

def parser_main():
    """
    Main function to process all recipe data files and save the results.
    """
    path_of_the_current_scripts_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir_path = os.path.join(path_of_the_current_scripts_dir, "partitioned_data")
    data_out_path = os.path.join(path_of_the_current_scripts_dir, "processed_data")
    
    os.makedirs(data_out_path, exist_ok=True)

    df_list = []

    # Loop through each CSV file in the input directory
    for file in os.listdir(data_dir_path):
        df = pd.read_csv(os.path.join(data_dir_path, file))
        df_list.append(process_data(df))

    # Concatenate all DataFrames into one and save it as JSON
    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        json_data = final_df.to_dict(orient='records')

        # Save final DataFrame as JSON
        with open(os.path.join(data_out_path, 'final_recipes_data.json'), 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

        # Save final DataFrame as a Parquet file
        parquet_file_path = os.path.join(data_out_path, 'final_recipes_data.parquet')
        final_df.to_parquet(parquet_file_path, index=False, engine='pyarrow')  # or engine='fastparquet'

    # Save sorted ingredients and units to JSON files
    with open(os.path.join(data_out_path, 'ingredients_calories_table.json'), 'w') as json_file:
        json.dump(sorted_ing_list, json_file, indent=4)

    with open(os.path.join(data_out_path, 'units_table.json'), 'w') as json_file:
        json.dump(sorted_unit_list, json_file, indent=4)


# Execute the main function when the script is run
if __name__ == "__main__":
    import time
    start_time = time.time()
    parser_main()
    print(f"Processing completed in {time.time() - start_time:.2f} seconds")
