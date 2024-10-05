import pandas as pd
import bisect
import re
import numpy as np
import ast
import unicodedata
import os
from fractions import Fraction

# Initialize an empty list to store ingredients in a sorted order
sorted_ing_list = []

def append_sorted(element):
    """
    Insert the ingredient element into the sorted_ing_list in a sorted manner based on the first two parts of the string.
    """
    # Convert the element to string to ensure uniformity
    element = str(element)
    
    # Extract the first two components of the ingredient string for comparison (e.g., "ingredient-unit")
    comparing_element = '-'.join(element.split('-')[:2])
    
    # Find the correct insertion index in the sorted list using binary search (for efficiency)
    index = bisect.bisect_left(sorted_ing_list, comparing_element)
    
    # Check if the element is already in the list based on the first two components
    if index < len(sorted_ing_list) and '-'.join(sorted_ing_list[index].split('-')[:2]) == comparing_element:
        return  # If the element already exists, do not add it again
    
    # Insert the element into the sorted list at the correct position
    sorted_ing_list.insert(index, element)

def parse_fraction(fraction_str):
    """
    Converts a fraction (string) to a float. Handles both whole numbers, fractions, and mixed fractions.
    """
    try:
        # If it's already a float or integer, return it as a float
        if isinstance(fraction_str, (float, int)):
            return float(fraction_str)

        # Handle mixed fractions like "5 1/2"
        if ' ' in fraction_str:
            whole_number, fraction_part = fraction_str.split()
            return float(int(whole_number) + Fraction(fraction_part))
        else:
            # Handle simple fractions like "1/2"
            return float(Fraction(fraction_str))

    except ValueError:
        # If conversion to a float fails, try to return it as a simple float
        try:
            return float(fraction_str)
        except (ValueError, TypeError):
            return None  # Return None for invalid inputs

def normalize_text(text):
    """
    Normalize text to remove any special characters, excessive spaces, and convert to a standard form.
    """
    # Normalize text using Unicode Normalization Form KD (NFKD)
    text = unicodedata.normalize('NFKD', text)
    # Replace multiple spaces with a single space and trim the text
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_total_time(directions):
    """
    Extracts the total time from the recipe instructions, which can include both minutes and hours.
    """
    total_minutes = 0  # Initialize total time in minutes
    
    # Loop through each step in the directions
    for step in directions:
        step = normalize_text(step)  # Normalize the step text
        
        # Use regex to find time expressions (e.g., "10 minutes", "2 hours")
        matches = re.findall(r'(\d+)\s*(minutes?|hours?)', step, flags=re.IGNORECASE)
        
        # Convert time expressions into minutes
        for amount, unit in matches:
            amount = int(amount)
            if 'hour' in unit.lower():
                amount *= 60  # Convert hours to minutes
            total_minutes += amount
    
    return int(total_minutes) if total_minutes > 0 else None  # Return total minutes or None if no time was found

def ing_parser(row):
    """
    Parses the ingredients, units, quantities, and nutrition information from a recipe row.
    Each ingredient's calories per unit is calculated and stored.
    """
    # Convert the 'Ingredients' column (a string representation of a list) into a Python list
    evaluatedIngList = ast.literal_eval(row['Ingredients'])
    
    # Assuming 'unit', 'quantity', and 'nutr_per_ingredient' are columns with lists of corresponding values
    for index, ing in enumerate(evaluatedIngList):
        ing = ing.split(', ')[0]  # Extract the main ingredient name by splitting on commas
        unit = ast.literal_eval(row['unit'])[index]  # Extract the unit
        
        # Parse the quantity, but handle invalid or None values
        quantity_raw = ast.literal_eval(row['quantity'])[index]
        quantity = parse_fraction(quantity_raw) if quantity_raw is not None else None
        
        if quantity is None or quantity == 0:
            continue  # Skip if quantity is invalid or zero
        
        # Extract calories for the ingredient and calculate per unit
        calories_of_ing = float(ast.literal_eval(row['nutr_per_ingredient'])[index]['nrg'])
        unit_calories = calories_of_ing / quantity if quantity else 0  # Avoid division by zero
        
        # Store the ingredient, unit, and calories in sorted order
        append_sorted(f'{ing}-{unit}-{str(unit_calories)}')

def process_data(df):
    """
    Process the recipe DataFrame by extracting total time, parsing ingredients, and calculating total calories.
    """
    # Extract total cooking time based on the instructions in the recipe
    df['Total Time'] = df.Instructions.apply(
        lambda val: extract_total_time([normalize_text(instr) for instr in ast.literal_eval(val)])
    )
    
    # Apply the ing_parser function to each row to process ingredients
    df.apply(lambda row: ing_parser(row), axis=1)
    
    # Calculate total calories by summing the 'nrg' field for all ingredients
    df['Calories'] = df.nutr_per_ingredient.apply(
        lambda val: np.sum([nutr['nrg'] for nutr in ast.literal_eval(val)])
    )
    
    # Return the DataFrame after dropping unnecessary columns
    return df.drop(['nutr_values_per100g', 'fsa_lights_per100g'], axis=1)

def main():
    """
    Main function that processes recipe data from CSV files, applies the necessary transformations,
    and saves the processed data along with a list of ingredients and their calories.
    """
    # Define the directory where the script is located
    path_of_the_current_scripts_dir = '/'.join(os.path.abspath(__file__).split('\\')[:-1])
    
    # Define the input and output directories for the data
    data_dir_path = os.path.join(path_of_the_current_scripts_dir, "partitioned_data")
    data_out_path = os.path.join(path_of_the_current_scripts_dir, "processed_data")
    
    # Create the output directory if it doesn't exist
    os.makedirs(data_out_path, exist_ok=True)
    
    # Loop through each CSV file in the input directory
    for file in os.listdir(data_dir_path):
        # Read the recipe data from the CSV file
        df = pd.read_csv(os.path.join(data_dir_path, file))
        
        # Process the data and save the results to a new CSV file
        process_data(df).to_csv(os.path.join(data_out_path, file), index=False)
    
    # Save the sorted ingredient-calories list to a NumPy binary file
    np.save(os.path.join(data_out_path, 'ingredients_calories_table.npy'), np.asarray(sorted_ing_list))

# Execute the main function when the script is run
if __name__ == "__main__":
    main()
