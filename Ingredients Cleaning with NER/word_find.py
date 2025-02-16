import re
import pandas as pd
import string

def normalize(word):
    # Karşılaştırma yaparken tüm alfasayısal olmayan karakterleri kaldırıyoruz.
    return ''.join(ch for ch in word if ch.isalnum())

def match_tokens_to_words(metin, tokens):
    # Ingredient içindeki orijinal kelimeleri (noktalama içeren) ve normalize edilmiş hallerini oluşturuyoruz.
    original_words = metin.split()
    norm_words = [normalize(word) for word in original_words]
    
    # Tokenlardan kelime gruplarını oluşturuyoruz.
    # "▁" işareti yeni kelime grubunun başlangıcı olarak kabul ediliyor.
    word_groups = []
    current = ""
    for token in tokens:
        token = token.strip()
        if token.startswith("▁"):
            if current:
                word_groups.append(current.strip())
            current = token.replace("▁", "")
        else:
            current += token.replace("▁", "")
    if current:
        word_groups.append(current.strip())
    
    matched_words = []
    
    for group in word_groups:
        norm_group = normalize(group)
        match = None
        
        # AŞAMA 1: Tek kelime eşleşmesi (tam veya kısmi)
        for orig, norm in zip(original_words, norm_words):
            if norm == norm_group:
                match = orig
                break
        if match is None:
            for orig, norm in zip(original_words, norm_words):
                if norm_group in norm:
                    match = orig
                    break
        
        # AŞAMA 2: Eğer tek kelime eşleşmesi bulunamadıysa, token grubunu ikiye bölüp bitişik iki kelime eşleşmesini ara.
        if match is None and norm_group:
            found_pair = None
            # Tüm olası bölme noktalarını deniyoruz.
            for i in range(1, len(norm_group)):
                part1 = norm_group[:i]
                part2 = norm_group[i:]
                # Ingredient içinde bitişik iki kelime arıyoruz.
                for j in range(len(norm_words) - 1):
                    # İlk kelime tam eşleşmeli, ikinci kelime içinde part2 bulunmalı.
                    if norm_words[j] == part1 and part2 in norm_words[j+1]:
                        found_pair = (original_words[j], original_words[j+1])
                        break
                if found_pair:
                    break
            if found_pair:
                # Bitişik kelime eşleşmesi bulundu: iki ayrı kelime olarak ekliyoruz.
                # Virgül karakterlerini kaldırarak orijinal haliyle ekliyoruz.
                matched_words.append(found_pair[0].replace(",", ""))
                matched_words.append(found_pair[1].replace(",", ""))
                continue  # Bu token grubunun işlenmesini tamamladık.
        
        # AŞAMA 3: Tek kelime için alt bölme eşleşmesi (heurstik)
        if match is None and norm_group:
            half = len(norm_group) // 2
            if half > 0:
                first_part = norm_group[:half]
                second_part = norm_group[half:]
                for orig, norm in zip(original_words, norm_words):
                    if norm.startswith(first_part) and norm.endswith(second_part):
                        match = orig
                        break
        
        if match is None:
            match = f"[{group}]"
        else:
            # Virgül karakterlerini çıktıdan kaldırıyoruz.
            match = match.replace(",", "")
        
        # Eğer aşamalardan birinde tek kelime eşleşmesi elde edildiyse, ekliyoruz.
        if isinstance(match, str):
            matched_words.append(match)
    
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
    

# Örnek çalıştırma
process_csv_pandas("parsed_name_tokens.tsv", "matched_name_tokens.tsv")
