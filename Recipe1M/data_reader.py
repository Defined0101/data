import ijson
import pandas as pd
import gc
import os

# Function to convert dictionary values to float (from Decimal, etc.)
def toDecimal(entries):
    out = {}
    for key, value in entries.items():
        out[key] = float(value)  # Convert each value to float
    return out

# Function to convert a list of dictionaries' values to float
def toDecimalArr(arr):
    outArr = []
    for entries in arr:
        out = {}
        for key, value in entries.items():
            out[key] = float(value)  # Convert each dictionary value to float
        outArr.append(out)  # Append the converted dictionary to output list
    return outArr

# Function to extract the 'text' field from a list of dictionaries
def process_fields(fields):
    arr = []
    for field in fields:
        arr.append(field['text'])  # Extract the 'text' field from each dictionary
    return arr

def main():
    # Define the directory where the script is located
    path_of_the_current_scripts_dir = '/'.join(os.path.abspath(__file__).split('\\')[:-1])

    # Create a directory to store partitioned data if it doesn't exist
    os.makedirs(os.path.join(path_of_the_current_scripts_dir, 'partitioned_data'), exist_ok=True)

    # Set the chunk size to split the data for each CSV file
    chunk_size = 10000

    # Open the JSON file containing the recipes data
    with open(os.path.join(path_of_the_current_scripts_dir, 'recipes_with_nutritional_info.json'), 'r') as file:
        # Use ijson to parse the file incrementally (streaming parsing)
        parser = ijson.items(file, 'item')  # 'item' must match the root structure of your JSON file

        # Create an empty DataFrame with specific columns for storing recipes
        recipes = pd.DataFrame(columns=['Name', 'Ingredients', 'Instructions', 'nutr_per_ingredient', 'fsa_lights_per100g', 'nutr_values_per100g', 'quantity', 'unit', 'weight_per_ingr'])

        # Loop through each entry in the parsed JSON
        for i, entry in enumerate(parser):
            # Process individual fields in the JSON entry
            ing = process_fields(entry['ingredients'])  # Get the list of ingredients
            ins = process_fields(entry['instructions'])  # Get the list of instructions
            qty = process_fields(entry['quantity'])  # Get the list of quantities
            unit = process_fields(entry['unit'])  # Get the list of units
            npi = toDecimalArr(entry['nutr_per_ingredient'])  # Convert 'nutr_per_ingredient' values to floats
            nvp = toDecimal(entry['nutr_values_per100g'])  # Convert 'nutr_values_per100g' to floats

            # Append the processed data into the DataFrame
            recipes.loc[len(recipes)] = {
                'Ingredients': ing,
                'Instructions': ins,
                'Name': entry['title'],
                'nutr_per_ingredient': npi,
                'fsa_lights_per100g': entry['fsa_lights_per100g'],
                'nutr_values_per100g': nvp,
                'quantity': qty,
                'unit': unit,
                'weight_per_ingr': list(map(float, entry['weight_per_ingr']))  # Convert weights to floats
            }

            # Save the data in chunks to prevent memory overload
            if (i + 1) % chunk_size == 0:
                # Save the current chunk of the DataFrame to a CSV file
                recipes.to_csv(os.path.join(path_of_the_current_scripts_dir, 'partitioned_data', f'recipes_{int((i + 1) / chunk_size)}.csv'), index=False)

                # Clear the DataFrame and perform garbage collection to free up memory
                del recipes
                gc.collect()

                # Reinitialize the DataFrame after each chunk
                recipes = pd.DataFrame(columns=['Name', 'Ingredients', 'Instructions', 'nutr_per_ingredient', 'fsa_lights_per100g', 'nutr_values_per100g', 'quantity', 'unit', 'weight_per_ingr'])

        # Save any remaining data that hasn't been saved yet
        if len(recipes) > 0:
            recipes.to_csv(os.path.join(path_of_the_current_scripts_dir, 'partitioned_data', f'recipes_{int((i + 2) / chunk_size)}.csv'), index=False)
            
            # Clear the DataFrame and perform garbage collection
            del recipes
            gc.collect()

if __name__ == "__main__":
    main()  # Execute the main function when the script is run
