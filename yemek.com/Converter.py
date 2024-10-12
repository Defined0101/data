import pandas as pd
import json
import re

def excel_to_custom_json(excel_file, output_file=None, sheet_name="Sheet1"):
    # Read the Excel file
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    #print(df)
    #for key, value in df.items():
        #print(value)
    recipe_name = df['Name']


    # Extract the necessary columns
    recipe_name = df['Name'].tolist()

    #print("recipe_name: ", type(recipe_name))

    description = df['Description'].tolist()
    total_time = df['Total_Time'].tolist()  
    calories = df['Calorie (/kcal)'].tolist() 
    protein = df['Protein'].tolist()
    fat = df['Fat'].tolist()
    carbohydrate = df['Carbohydrate'].tolist()
    instructions = df['Instructions'].tolist()

    # Extract ingredient details
    
    ingredients = []
    for index, row in df.iterrows():
        #print("index: ", index+2)
        names = row["Ingredients:"]
        quantities = row["Quantities"]
        units = row["Units"]

        names_splited = names.split(',')
        name_list = [name_clean.strip() for name_clean in names_splited]

        quantity_list = quantities.split(',')
        
        units_splited = units.split(',')
        unit_list = [unit_clean.strip() for unit_clean in units_splited]


        #print("quantity: ", quantity_list)
        #print("quantity: ", type(quantity_list))

        length = len(name_list)
        length2 = len(quantity_list)
        length3 = len(unit_list)
        #print("name_list: ", name_list)
        #print("length: ", length, "length2: ", length2, "length3: ", length3)

        lengths = {length, length2, length3}

        #print("name: ", recipe_name[index])
        if len(lengths) != 1:
            quantity_list = normalize_numbers(quantities)
            #print("name_list: ", name_list)
            #print("quantity_list:", quantity_list)
            length2 = len(quantity_list)
            #print("fixed length2: ", length2)
            lengths = {length, length2, length3}
            if len(lengths) != 1:
                #print("index error: ", index+2)
                #print("name: ", recipe_name[index])
                print("yoooooooooooooooooooooooooook")
                # should be deleted from excel. because they contains ',' in () which is not necessary.
                # 560 and 604 are fixed in yoresel-tarifler.
                continue
        else:
            quantity_splited = quantities.split(',')
            quantity_list = [quantity_clean.strip() for quantity_clean in quantity_splited]

        ingredients_list = []
        for i in range(length):
            
            ingredient = {
                "name": name_list[i],
                "quantity": quantity_list[i],
                "unit": unit_list[i]
            }
            #print("ingredient: ", ingredient)
            ingredients_list.append(ingredient)
        ingredients.append(ingredients_list)

    if (len(ingredients) != len(recipe_name)):
        print("Something is wrong!!!!")
    
    #print("ingredients_list: ", type(ingredients_list))
    # Create the final structure in JSON
    recipes = []
    for i in range(len(recipe_name)):
        recipe = {
            "name": recipe_name[i],
            "instructions": instructions[i],
            "ingredients": ingredients[i],
            "total_time": total_time[i],
            "calories": calories[i],
            "fat": fat[i],
            "protein": protein[i],
            "carbohydrate": carbohydrate[i],
            "desc": description[i]
        }
        recipes.append(recipe)

    #print(recipe)

    # Convert the structure to JSON
    json_data = json.dumps(recipes, ensure_ascii=False, indent=4)

    # Save the JSON to a file, if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json_file.write(json_data)
        print(f"Data saved to {output_file}")
    
    return json_data

def normalize_numbers(data_string):
    # Replace any occurrence of a number followed by a comma and another number
    normalized_string = re.sub(r'(\d),(\d)', r'\1.\2', data_string)
    
    # Step 2: Split the normalized string by commas
    data_splited = normalized_string.split(',')
    data_list = [data_clean.strip() for data_clean in data_splited]

    # Step 3: Convert the strings to floats
    normalized_data = []
    for value in data_list:
        normalized_value = value.strip()  # Remove any leading/trailing spaces
        try:
            normalized_value = float(normalized_value)
        except ValueError:
            pass  # If conversion fails, keep it as a string
        
        normalized_data.append(normalized_value)

    return normalized_data

excel_files = ["zeytinyaglilar", "yoresel-tarifler", "kahvaltiliklar"]

"""for file in excel_files:
    excel_file = f"{file}.xlsx"
    output_file = f"recipe_data_{file}.json"
    json_data = excel_to_custom_json(excel_file, output_file=output_file)"""

# Example usage
excel_file = 'zeytinyaglilar.xlsx'
output_file = 'recipe_data_zeytinyaglilar.json'
json_data = excel_to_custom_json(excel_file, output_file=output_file)
#print(json_data)
