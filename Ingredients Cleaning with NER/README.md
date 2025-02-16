data.ipynb: This notebok for pre-cleaning steps. Then, data will be ready for NER model.

parser.py: This code for extracting NER model outputs according to labels of tokens.

word_find.py: This code for creating words from selected tagged tokens.

words_combine.py: This code combines candidate words according to original text.

handle_problematic_ingredients.ipynb: This notebook seperates recipes which have more than 4 words for their cleanned names of ingredients. Also, it deletes recipes which do not have any valid 
ingredients or are not a valid recipe.

changed_ingredient_names.ipynb: This notebook changes ingredients names with their cleanned form.
