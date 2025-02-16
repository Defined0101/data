import pandas as pd

def en_uzun_tam_eslesme(satir):
    ingredient = satir['Ingredient']
    matched_words_raw = satir['Matched Words']
    
    if not isinstance(matched_words_raw, str) or not matched_words_raw.strip():
        return None

    # Aday kelimeleri oluştururken, boşlukları temizleyip küçük harfe çeviriyoruz.
    # Ayrıca, "[" veya "]" içeren adaylar filtreleniyor.
    matched_words = [
        mw.strip().lower() 
        for mw in matched_words_raw.split(',')
        if mw.strip() and ('[' not in mw and ']' not in mw)
    ]
    
    if not matched_words:
        return None

    # Orijinal metni küçük harfe çeviriyoruz ki eşleşmeler hatasız olsun.
    ingredient_lower = ingredient.lower()
    
    # Aday kelimelerin sırasına göre ilk ve son kelimeyi alıyoruz.
    first_candidate = matched_words[0]
    last_candidate = matched_words[-1]
    
    # İlk aday kelimenin orijinal metinde ilk geçtiği yeri buluyoruz.
    first_index = ingredient_lower.find(first_candidate)
    # Son aday kelimenin orijinal metinde son geçtiği yeri buluyoruz.
    last_index = ingredient_lower.rfind(last_candidate)
    
    if first_index == -1 or last_index == -1:
        return None
    if first_index > last_index:
        return None  # İlk aday kelime, son aday kelimeden sonra geliyorsa mantıklı bir eşleşme yok.

    # Son aday kelimenin tamamını kapsayacak şekilde son indis.
    end_index = last_index + len(last_candidate)
    
    # İlk aday kelimenin başladığı yerden son aday kelimenin bitişine kadar olan kısmı alıyoruz.
    selected_phrase = ingredient_lower[first_index:end_index]
    
    return selected_phrase if selected_phrase else None


if __name__ == "__main__":
    dosya_yolu = "matched_name_tokens.tsv"  
    veri = pd.read_csv(dosya_yolu, sep="\t", dtype=str).fillna('')  

    veri['En Uzun Tam Eşleşme'] = veri.apply(en_uzun_tam_eslesme, axis=1)
    veri.to_csv("tam_eslesme_sonuclari.tsv", sep="\t", index=False, encoding="utf-8")
    print("İşlem tamamlandı. 'tam_eslesme_sonuclari.tsv' dosyası oluşturuldu.")
