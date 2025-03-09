# Recipe Search and Recommendation System

Bu sistem, tarif arama ve öneri sistemi olarak çalışır. Qdrant vektör veritabanını kullanarak metin tabanlı aramalar ve benzerlik bazlı öneriler sunar.

## Özellikler

- Metin tabanlı tarif arama
- ID bazlı tarif arama
- Benzer tarifleri bulma
- Kullanıcı bazlı tarif önerileri
- Embedding tabanlı benzerlik hesaplama

## Kurulum

### Gereksinimler
```bash
pip install qdrant-client
pip install torch
pip install transformers
pip install pandas
pip install pyarrow
```

### Veri Hazırlığı
- `recipes.parquet` dosyası gereklidir
- Qdrant sunucusu çalışır durumda olmalıdır
- Tarif embedding'leri Qdrant'a yüklenmiş olmalıdır

## Kullanım

### 1. Metin Bazlı Arama
```python
# Metin ile tarif arama
search_recipes(query="The Best Blts", query_type="text")
```

### 2. ID ile Arama
```python
# ID ile tarif arama
search_recipes(query=5, query_type="id")
```

### 3. Benzerlik Parametreleri
```python
# Benzerlik eşikleri ile arama
search_recipes(
    query="Pizza",
    query_type="text",
    similarity_threshold=0.5,  # Minimum benzerlik skoru
    upper_threshold=0.99,      # Maksimum benzerlik skoru
    limit=10                   # Sonuç sayısı
)
```

### 4. Kullanıcı Bazlı Öneriler
```python
# Kullanıcı için tarif önerileri
recommend_test_user_recipes(user_id=101, limit=3)
```

## Fonksiyonlar

### search_recipes()
```python
def search_recipes(query=None, query_type="text", limit=10, 
                  similarity_threshold=0.0, upper_threshold=None)
```
- `query`: Aranacak metin veya ID
- `query_type`: "text" veya "id"
- `limit`: Maksimum sonuç sayısı
- `similarity_threshold`: Minimum benzerlik skoru
- `upper_threshold`: Maksimum benzerlik skoru

### recommend_test_user_recipes()
```python
def recommend_test_user_recipes(user_id, limit=3)
```
- `user_id`: Öneri yapılacak kullanıcı ID'si
- `limit`: Önerilecek tarif sayısı

## Çıktı Formatı

## Notlar

- Sistem BAAI/bge-en-icl modelini kullanır
- Embedding'ler otomatik normalize edilir
- Arama sonuçları benzerlik skorlarına göre sıralanır
- Kullanıcı önerileri, benzer kullanıcıların beğenilerine dayanır

## Hata Yönetimi

- Geçersiz sorgu tipleri için uyarı verir
- Bulunamayan tarifler için bilgi mesajı gösterir
- Embedding hesaplama/yükleme hataları için hata mesajları gösterir

## Performans

- Sık kullanılan sorgular için önbellek kullanır
- Batch işlemler için optimize edilmiştir
- CUDA desteği mevcuttur (kullanılabilirse)