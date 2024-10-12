import ijson
import pandas as pd
import gc
import os

# Function to convert dictionary values to float (from Decimal, etc.)
def toDecimal(entries):
    return {key: float(value) for key, value in entries.items()}

# Function to convert a list of dictionaries' values to float
def toDecimalArr(arr):
    return [{key: float(value) for key, value in entries.items()} for entries in arr]

# Function to extract the 'text' field from a list of dictionaries
def process_fields(fields):
    return [field['text'] for field in fields]

def reader_main():
    # Define the directory where the script is located
    path_of_the_current_scripts_dir = os.path.dirname(os.path.abspath(__file__))

    # Create a directory to store partitioned data if it doesn't exist
    os.makedirs(os.path.join(path_of_the_current_scripts_dir, '../', 'nutr_partitioned_data'), exist_ok=True)

    # Set the chunk size to split the data for each CSV file
    chunk_size = 10000

    # Initialize a list to store data temporarily before converting to a DataFrame
    temp_data = []

    counter = 0

    # Open the JSON file containing the recipes data
    with open(os.path.join(path_of_the_current_scripts_dir, '../', 'recipes_with_nutritional_info.json'), 'r') as file:
        # Use ijson to parse the file incrementally (streaming parsing)
        parser = ijson.items(file, 'item')  # 'item' must match the root structure of your JSON file

        # Loop through each entry in the parsed JSON
        for i, entry in enumerate(parser):
            counter += 1
            # Process individual fields in the JSON entry
            ing = process_fields(entry['ingredients'])  # Get the list of ingredients
            ins = process_fields(entry['instructions'])  # Get the list of instructions
            qty = process_fields(entry['quantity'])  # Get the list of quantities
            unit = process_fields(entry['unit'])  # Get the list of units
            npi = toDecimalArr(entry['nutr_per_ingredient'])  # Convert 'nutr_per_ingredient' values to floats
            nvp = toDecimal(entry['nutr_values_per100g'])  # Convert 'nutr_values_per100g' to floats

            # Append the processed data into the temp_data list
            temp_data.append({
                'Name': entry['title'],
                'Ingredients': ing,
                'Instructions': ins,
                'nutr_per_ingredient': npi,
                'fsa_lights_per100g': entry['fsa_lights_per100g'],
                'nutr_values_per100g': nvp,
                'quantity': qty,
                'unit': unit,
                'weight_per_ingr': list(map(float, entry['weight_per_ingr']))  # Convert weights to floats
            })

            # Save the data in chunks to prevent memory overload
            if (i + 1) % chunk_size == 0:
                # Convert the temp_data list to a DataFrame
                recipes_chunk = pd.DataFrame(temp_data)

                # Save the current chunk of the DataFrame to a CSV file
                recipes_chunk.to_csv(os.path.join(path_of_the_current_scripts_dir, '../', 'nutr_partitioned_data', f'recipes_{int((i) / chunk_size)}.csv'), index=False)

                # Clear the temp_data list and perform garbage collection to free up memory
                temp_data.clear()
                gc.collect()

        # Save any remaining data that hasn't been saved yet
        if len(temp_data) > 0:
            # Convert the remaining temp_data list to a DataFrame
            recipes_chunk = pd.DataFrame(temp_data)

            # Save to CSV
            recipes_chunk.to_csv(os.path.join(path_of_the_current_scripts_dir, '../', 'nutr_partitioned_data', f'recipes_{int((i + 1) / chunk_size)}.csv'), index=False)
            
            # Clear the temp_data list and perform garbage collection
            temp_data.clear()
            gc.collect()
    
    return counter

if __name__ == "__main__":
    import time
    start_time = time.time()
    count = reader_main()  # Execute the main function when the script is run
    print(f"Processing completed in {time.time() - start_time:.2f} seconds")
    print(f"{count} recipes have been read")
