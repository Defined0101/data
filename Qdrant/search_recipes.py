import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct
import ast
import torch.nn.functional as F
import atexit
from functools import lru_cache
import signal



# Qdrant bağlantısı
client = QdrantClient("localhost", port=6333, timeout=300, prefer_grpc=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model ve tokenizer'ı global olarak bir kere yükleyelim ve device'a taşıyalım
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-en-icl")
model = AutoModel.from_pretrained("BAAI/bge-en-icl").to(device)
model.eval()  # Modeli eval moduna alalım

# Tarif verilerini yükle
recipes_df = pd.read_parquet("recipes.parquet", engine="pyarrow")
print("Tarif kolonları:", recipes_df.columns)

# Cleanup fonksiyonunu güncelleyelim
def cleanup():
    """
    Program sonlandığında kaynakları düzgün bir şekilde temizler.
    """
    try:
        # Önce model ve tokenizer'ı temizle
        model.cpu()  # GPU belleğini temizle
        torch.cuda.empty_cache()  # CUDA önbelleğini temizle
        
        # Qdrant client'ı kapat
        if hasattr(client, '_channel'):
            client._channel.close()
        if hasattr(client, 'grpc_channel'):
            client.grpc_channel.close()
        client.close()
        
    except Exception as e:
        print(f"Cleanup sırasında hata oluştu: {e}")
    finally:
        # Tüm CUDA kaynakklarını temizle
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# Cleanup fonksiyonunu program çıkışına ve SIGINT (Ctrl+C) sinyaline kaydet
atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s, f: cleanup())




# Text embedding fonksiyonunu optimize edelim
@torch.no_grad()  # Context manager yerine decorator kullanalım
def get_text_embedding(text):
    """
    Verilen metni embedding'e çevirir.
    """
    inputs = tokenizer(
        text, 
        return_tensors="pt", 
        padding=True, 
        truncation=True,
        max_length=512  # Maksimum uzunluğu sınırlayalım
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    outputs = model(**inputs)
    embedding = outputs.last_hidden_state[:, -1, :]
    embedding = F.normalize(embedding, p=2, dim=1)

    return embedding.squeeze().cpu().numpy()

# Sık aranan metinler için önbellek ekleyelim
@lru_cache(maxsize=1000)  # Son 1000 sorguyu önbellekte tutalım
def cached_get_text_embedding(text):
    """
    Metni embedding'e çevirir ve sonucu önbellekte saklar.
    """
    return get_text_embedding(text)

def get_recipe_id(query_text):
    """
    Kullanıcının girdiği query_text'i en yakın tarifin id'sini döndürür.
    """
    # Önce query_text'e en benzer yemek ismini bulalım
    query_vector = get_text_embedding(query_text)
    
    search_response = client.query_points(
        collection_name="text_embeddings",
        query=query_vector.tolist(),
        limit=1,  # En yakın tek tarifi al
        with_payload=True
    )
    
    # Eğer en yakın tarif bulunamazsa None döndür
    if not search_response.points:
        return None

    # En yakın tarifin ID'sini döndür
    return search_response.points[0].id


def search_recipes(query=None, query_type="text", limit=10, similarity_threshold=0.0, upper_threshold=None):
    """
    Verilen sorgu ile benzer tarifleri bulur.
    
    Args:
        query: Aranacak metin veya ID
        query_type: Sorgu tipi ("text" veya "id")
        limit: Döndürülecek maksimum sonuç sayısı
        similarity_threshold: Minimum benzerlik skoru
        upper_threshold: Maksimum benzerlik skoru
    """
    try:
        if query is None:
            print("Lütfen bir sorgu (query) belirtin.")
            return
            
        recipe_id = None
        
        if query_type == "text":
            # Önbellekli embedding fonksiyonunu kullanalım
            query_vector = cached_get_text_embedding(query)
            search_response = client.query_points(
                collection_name="text_embeddings",
                query=query_vector.tolist(),
                limit=1,
                with_payload=True
            )
            
            if not search_response.points:
                print("Sorgu metni için eşleşen tarif bulunamadı.")
                return
                
            recipe_id = search_response.points[0].id
            print(f"\nArama Sonuçları: '{query}' metni için bulunan tarif ve benzerleri")
            
        elif query_type == "id":
            recipe_id = query
            print(f"\nArama Sonuçları: ID {query} ile benzer tarifler")
        else:
            print("Geçersiz sorgu tipi. 'text' veya 'id' kullanın.")
            return
            
        # ID ile benzer tarifleri bul
        recommend_response = client.recommend(
            collection_name="text_embeddings",
            positive=[recipe_id],
            limit=limit,
            with_payload=True
        )
        
        hits = recommend_response if isinstance(recommend_response, list) else recommend_response.points
        print("-" * 50)
        
        for point in hits:
            if similarity_threshold is not None and point.score < similarity_threshold:
                continue
            if upper_threshold is not None and point.score > upper_threshold:
                continue
                
            try:
                matching_recipes = recipes_df[recipes_df['ID'] == point.id]
                if not matching_recipes.empty:
                    recipe = matching_recipes.iloc[0]
                    print(f"Tarif Adı: {recipe['Name']}")
                    print(f"Kategori: {recipe['Category']}")
                    print(f"Benzerlik Skoru: {point.score:.4f}")
                    print("-" * 50)
                else:
                    print(f"Tarif bulunamadı (ID: {point.id})")
            except Exception as e:
                print(f"Sonuç işleme hatası: {str(e)}")
                
    except Exception as e:
        print(f"Arama sırasında bir hata oluştu: {str(e)}")


# Test için kullanıcıların beğendiği tarifleri simüle edelim
test_user_interactions = {
    101: [5, 13, 27],  # Kullanıcı 101 -> Tarif ID'leri 5, 12, 27'yi beğenmiş
    102: [9, 13, 19],  # Kullanıcı 102 -> Tarif ID'leri 8, 12, 19'u beğenmiş
    103: [4, 9, 27]   # Kullanıcı 103 -> Tarif ID'leri 3, 8, 27'yi beğenmiş
}

# Kullanıcıların embeddinglerini test için hesaplayalım
test_user_embeddings = {}

def get_recipe_embedding(recipe_id):
    """
    Tarif ID'si için embedding'i alır.
    """
    try:
        point = client.retrieve(
            collection_name="text_embeddings",
            ids=[recipe_id],
            with_vectors=True
        )
        if point and point[0].vector:
            return point[0].vector
    except Exception as e:
        print(f"Tarif embedding'i alınırken hata: {e}")
    return None

def calculate_user_embeddings():
    """
    Test kullanıcıları için embedding'leri hesaplar.
    """
    print("\nKullanıcı embedding'leri hesaplanıyor...")
    calculated_embeddings = {}
    
    for user_id, recipe_ids in test_user_interactions.items():
        recipe_embeddings = []
        print(f"\nKullanıcı {user_id} için tarif embedding'leri alınıyor:")
        
        for recipe_id in recipe_ids:
            recipe_vector = get_recipe_embedding(recipe_id)
            if recipe_vector is not None:
                recipe_embeddings.append(recipe_vector)
                print(f"Tarif ID {recipe_id} embedding'i alındı")
        
        if recipe_embeddings:
            calculated_embeddings[user_id] = torch.tensor(recipe_embeddings).mean(dim=0).numpy()
            print(f"Kullanıcı {user_id} embedding'i oluşturuldu")
    
    return calculated_embeddings

def store_test_user_embeddings():
    """
    Test kullanıcı embedding'lerini Qdrant'a yükler.
    """
    try:
        # Önce koleksiyonun var olup olmadığını kontrol et
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]
        
        # Eğer koleksiyon yoksa oluştur
        if "test_user_embeddings" not in collection_names:
            client.create_collection(
                collection_name="test_user_embeddings",
                vectors_config=VectorParams(
                    size=4096,
                    distance="Cosine"
                )
            )
            print("'test_user_embeddings' koleksiyonu oluşturuldu.")
        
        # PointStruct kullanarak points listesi oluştur
        test_embeddings = [
            PointStruct(
                id=int(user_id),
                vector=embedding.tolist(),
                payload={"user_id": int(user_id)}
            )
            for user_id, embedding in test_user_embeddings.items()
        ]

        if test_embeddings:  # Boş liste kontrolü
            client.upsert(
                collection_name="test_user_embeddings",
                points=test_embeddings,
                wait=True
            )
            print(f"Test kullanıcı embedding'leri yüklendi: {len(test_embeddings)} kullanıcı.")
        else:
            print("Yüklenecek embedding bulunamadı.")
            
    except Exception as e:
        print(f"Test kullanıcı embedding'leri yüklenirken hata oluştu: {e}")

def find_similar_users(test_user_id, top_n=3):
    """
    Test kullanıcısına en benzer kullanıcıları bulur.
    """
    if test_user_id not in test_user_embeddings:
        print(f"Kullanıcı {test_user_id} için embedding bulunamadı.")
        return []

    user_embedding = test_user_embeddings[test_user_id]

    search_response = client.query_points(
        collection_name="test_user_embeddings",
        query=user_embedding.tolist(),
        limit=top_n,
        with_payload=True
    )

    similar_users = [hit.payload["user_id"] for hit in search_response.points if hit.payload["user_id"] != test_user_id]
    print(f"Kullanıcı {test_user_id} için en benzer {top_n} kullanıcı: {similar_users}")
    return similar_users

def recommend_test_user_recipes(user_id, limit=3):
    """
    Test kullanıcısına benzer kullanıcıların beğendiği tarifleri önerir.
    """
    similar_users = find_similar_users(user_id)

    if not similar_users:
        print(f"Kullanıcı {user_id} için öneri yapılamadı.")
        return []

    recommended_recipes = []
    for similar_user in similar_users:
        recommended_recipes.extend(test_user_interactions.get(similar_user, []))

    top_recipes = pd.Series(recommended_recipes).value_counts().head(limit).index.tolist()
    print(f"Kullanıcı {user_id} için önerilen tarifler: {top_recipes}")
    return top_recipes


if __name__ == "__main__":
    # Mevcut test kodları
    #print("ID ile arama örneği:")
    #search_recipes(query=5, query_type="id", upper_threshold=0.99)
    
    #print("\nMetin ile arama örneği:")
    #search_recipes(query="The Best Blts", query_type="text", upper_threshold=0.99)
    
    # Yeni test kodları
    print("\nTest kullanıcı embeddingleri oluşturuluyor...")
    test_user_embeddings = calculate_user_embeddings()
    store_test_user_embeddings()
    
    print("\nKullanıcı önerileri testi:")
    recommend_test_user_recipes(101)