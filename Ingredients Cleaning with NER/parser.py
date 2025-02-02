import re
import json
import pandas as pd

def clean_prediction(prediction):
    try:
        prediction = prediction.replace("'", "\"")
        prediction = re.sub(r'}\s*{', '},{', prediction)
        if not prediction.startswith("[") and not prediction.endswith("]"):
            prediction = f"[{prediction}]"
        json.loads(prediction)  
        return prediction
    except Exception:
        return None

def parse_i_name_tokens_pandas(input_csv, output_csv, error_csv):
    df = pd.read_csv(input_csv, sep="\t", dtype=str)  
    df = df.fillna('')  

    df["I-NAME tokens"] = ""
    df["error"] = ""

    success_rows = []
    error_rows = []

    for index, row in df.iterrows():
        ingredient = row.get("Ingredient", "").strip()
        ids = row.get("IDs", "").strip()
        index_level = row.get("__index_level_0__", "").strip()
        prediction = row.get("prediction", "").strip()

        i_name_tokens = []  

        try:
            if prediction:
                cleaned_prediction = clean_prediction(prediction)
                if cleaned_prediction:  
                    parsed_list = json.loads(cleaned_prediction)
                    for token_dict in parsed_list:
                        if isinstance(token_dict, dict) and token_dict.get('entity') == 'I-NAME':
                            word_val = token_dict.get('word', '').strip()
                            if word_val:
                                i_name_tokens.append(word_val)
                    df.at[index, "I-NAME tokens"] = ", ".join(i_name_tokens)
                else:
                    raise ValueError("Prediction temizlenemedi")
        except Exception as e:
            error_rows.append({
                "Ingredient": ingredient,
                "IDs": ids,
                "__index_level_0__": index_level,
                "prediction": prediction,
                "error": str(e)
            })
            continue  

        success_rows.append({
            "Ingredient": ingredient,
            "IDs": ids,
            "__index_level_0__": index_level,
            "I-NAME tokens": ", ".join(i_name_tokens)
        })

    success_df = pd.DataFrame(success_rows)
    success_df.to_csv(output_csv,sep="\t", index=False, encoding="utf-8")

    error_df = pd.DataFrame(error_rows)
    error_df.to_csv(error_csv, index=False, encoding="utf-8")

    print(f"İşlem tamamlandı: {len(success_df)} başarılı, {len(error_df)} hata bulundu.")
    print(f"Sonuç kaydedildi: {output_csv}")
    print(f"Hatalı satırlar kaydedildi: {error_csv}")

parse_i_name_tokens_pandas("output.tsv", "parsed_name_tokens.tsv", "errors.csv")
