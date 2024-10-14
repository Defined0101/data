"""
this file is for fixing unnecessary words in Units and Ingredients sections.
"""
import json

# List of words/phrases to be removed
unwanted_words = ["büyük boy", "büyük", "küçük boy", "küçük", "orta boy", "orta"]

def clean_text(text):
    # Remove unwanted words/phrases
    for word in unwanted_words:
        text = text.replace(word, "").strip()  # Remove the word and trim spaces
    return text

def clean_json_data(data):
    # Check if it's a list or a dictionary
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                # Clean text if it's a string (e.g., ingredients or Units)
                data[key] = clean_text(value)
            elif isinstance(value, (list, dict)):
                # Recursively clean if it's a nested list or dictionary
                clean_json_data(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, str):
                data[index] = clean_text(item)
            elif isinstance(item, (list, dict)):
                clean_json_data(item)

input_file = "save/recipe_data_zeytinyaglilar.json"
cleaned_file = "clean_zeytinyaglilar.json"
# Load JSON file
with open(input_file, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Clean the data
clean_json_data(json_data)

# Save the cleaned data to a new JSON file
with open(cleaned_file, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)

print(f"File cleaned and saved as {cleaned_file}")
