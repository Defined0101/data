import pandas as pd
import re

def match_tokens_to_words(metin, tokens):
    words = metin.split()  
    matched_words = []
    candidate_tokens = []

    for token in tokens:
        token = token.strip() 

        if token.startswith("▁"):
            if candidate_tokens:
                candidate_word = "".join(candidate_tokens).replace("▁", "").strip()
                if candidate_word in words:
                    matched_words.append(candidate_word)
                else:
                    partial_match = [word for word in words if candidate_word in word]
                    if partial_match:
                        matched_words.append(partial_match[0])
                    else:
                        matched_words.append(f"[{candidate_word}]")  
                candidate_tokens = []  

        candidate_tokens.append(token.replace("▁", ""))  

    if candidate_tokens:
        candidate_word = "".join(candidate_tokens).strip()
        if candidate_word in words:
            matched_words.append(candidate_word)
        else:
            partial_match = [word for word in words if candidate_word in word]
            if partial_match:
                matched_words.append(partial_match[0])
            else:
                matched_words.append(f"[{candidate_word}]")

    return matched_words

def process_csv_pandas(input_csv, output_csv):
    df = pd.read_csv(input_csv, sep="\t", dtype=str)  
    df = df.fillna('')  

    df["Matched Words"] = ""

    for index, row in df.iterrows():
        ingredient = row.get("Ingredient", "").strip()
        tokens = row.get("I-NAME tokens", "").split(", ")  

        matched_words = match_tokens_to_words(ingredient, tokens)

        df.at[index, "Matched Words"] = ", ".join(matched_words)

    df.to_csv(output_csv, sep="\t", index=False, encoding="utf-8")

    print(f"İşlem tamamlandı, eşleşen kelimeler {output_csv} dosyasına kaydedildi.")

process_csv_pandas("parsed_name_tokens.tsv", "matched_name_tokens.tsv")
