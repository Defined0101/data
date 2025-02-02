import pandas as pd
import nltk
import string

NOUN_TAGS = {"NN", "NNS", "NNP", "NNPS"}

def remove_punctuation(text):
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator).strip()

def is_noun_or_derivative(word):
    tokens = nltk.word_tokenize(word)
    if not tokens:
        return False
    
    pos_tags = nltk.pos_tag(tokens)  
    return pos_tags[0][1] in NOUN_TAGS

def last_word_is_noun(phrase):
    tokens = nltk.word_tokenize(phrase)
    if not tokens:
        return False
    
    pos_tags = nltk.pos_tag([tokens[-1]])  
    return pos_tags[0][1] in NOUN_TAGS

def en_uzun_tam_eslesme(satir):
    ingredient = satir['Ingredient']
    matched_words_raw = satir['Matched Words']
    
    if not isinstance(matched_words_raw, str) or not matched_words_raw.strip():
        return None

    matched_words_temp = matched_words_raw.split(',')
    matched_words = [
        remove_punctuation(mw).lower()  
        for mw in matched_words_temp
        if remove_punctuation(mw).strip()
    ]

    if not matched_words:
        return None
    
    original_tokens = nltk.word_tokenize(ingredient)
    normalized_tokens = [remove_punctuation(tok).lower() for tok in original_tokens]
    token_pairs = list(zip(original_tokens, normalized_tokens))
    
    first_word_norm = matched_words[0]
    last_word_norm = matched_words[-1]
    
    try:
        first_index = next(
            i for i, (orig, norm) in enumerate(token_pairs)
            if norm == first_word_norm
        )
    except StopIteration:
        return None  
    
    try:
        last_index = len(token_pairs) - 1 - next(
            i for i, (orig, norm) in enumerate(reversed(token_pairs))
            if norm == last_word_norm
        )
    except StopIteration:
        return None
    
    if first_index > last_index:
        first_index, last_index = last_index, first_index
    
    selected_pairs = token_pairs[first_index:last_index+1]
    
    selected_phrase = ' '.join(norm for (orig, norm) in selected_pairs if norm)

    return selected_phrase if selected_phrase else None


if __name__ == "__main__":
    dosya_yolu = "matched_name_tokens.tsv"  
    veri = pd.read_csv(dosya_yolu, sep="\t", dtype=str).fillna('')  

    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    
    veri['En Uzun Tam Eşleşme'] = veri.apply(en_uzun_tam_eslesme, axis=1)
    
    veri.to_csv("tam_eslesme_sonuclari.tsv", sep="\t", index=False, encoding="utf-8")
    print("İşlem tamamlandı. 'tam_eslesme_sonuclari.tsv' dosyası oluşturuldu.")
