import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams
import time
import gc
import logging
import os
# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qdrant_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def upload_data_to_qdrant():
    try:
        # 1. Adım: İlk veri setini yükle

        current_dir = os.path.dirname(os.path.abspath(__file__))
        gpu0_file = os.path.join(current_dir, "recipe_data_gpu0.npz")
        gpu1_file = os.path.join(current_dir, "recipe_data_gpu1.npz")

        logger.info("GPU0 verisi yükleniyor...")
        data_gpu0 = np.load(gpu0_file)
        ids0 = data_gpu0["ids"]
        embeddings0 = data_gpu0["embeddings"]
        del data_gpu0
        gc.collect()

        # Qdrant bağlantısı
        client = QdrantClient(
            "localhost", 
            port=6333,
            timeout=300,
            prefer_grpc=True
        )

        # Koleksiyon oluştur
        vector_size = embeddings0.shape[1]
        if client.collection_exists("text_embeddings"):
            client.delete_collection("text_embeddings")

        client.create_collection(
            collection_name="text_embeddings",
            vectors_config=VectorParams(
                size=vector_size,
                distance="Cosine"
            )
        )

        # İlk veri setini yükle
        BATCH_SIZE = 25
        total_points = len(ids0)
        batch_count = (total_points + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info("GPU0 verisi Qdrant'a yükleniyor...")
        for batch_idx in range(batch_count):
            try:
                start_idx = batch_idx * BATCH_SIZE
                end_idx = min((batch_idx + 1) * BATCH_SIZE, total_points)
                
                batch_ids = ids0[start_idx:end_idx]
                batch_embeddings = embeddings0[start_idx:end_idx]
                
                batch_points = [
                    PointStruct(
                        id=int(id_),
                        vector=emb.tolist(),
                        payload={"recipe_id": int(id_)}
                    )
                    for id_, emb in zip(batch_ids, batch_embeddings)
                ]
                
                client.upsert(
                    collection_name="text_embeddings",
                    points=batch_points,
                    wait=True
                )
                
                logger.info(f"GPU0 Batch {batch_idx + 1}/{batch_count} yüklendi.")
                
                del batch_points, batch_ids, batch_embeddings
                gc.collect()
                
            except Exception as e:
                logger.error(f"GPU0 Batch yüklenirken hata: {str(e)}")
                time.sleep(2)
                continue

        # İlk veri setini temizle
        del ids0, embeddings0
        gc.collect()

        # 2. Adım: İkinci veri setini yükle
        logger.info("GPU1 verisi yükleniyor...")
        data_gpu1 = np.load(gpu1_file)
        ids1 = data_gpu1["ids"]
        embeddings1 = data_gpu1["embeddings"]
        del data_gpu1
        gc.collect()

        # İkinci veri setini yükle
        total_points = len(ids1)
        batch_count = (total_points + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info("GPU1 verisi Qdrant'a yükleniyor...")
        for batch_idx in range(batch_count):
            try:
                start_idx = batch_idx * BATCH_SIZE
                end_idx = min((batch_idx + 1) * BATCH_SIZE, total_points)
                
                batch_ids = ids1[start_idx:end_idx]
                batch_embeddings = embeddings1[start_idx:end_idx]
                
                batch_points = [
                    PointStruct(
                        id=int(id_),
                        vector=emb.tolist(),
                        payload={"recipe_id": int(id_)}
                    )
                    for id_, emb in zip(batch_ids, batch_embeddings)
                ]
                
                client.upsert(
                    collection_name="text_embeddings",
                    points=batch_points,
                    wait=True
                )
                
                logger.info(f"GPU1 Batch {batch_idx + 1}/{batch_count} yüklendi.")
                
                del batch_points, batch_ids, batch_embeddings
                gc.collect()
                
            except Exception as e:
                logger.error(f"GPU1 Batch yüklenirken hata: {str(e)}")
                time.sleep(2)
                continue

        # Son temizlik
        del ids1, embeddings1
        gc.collect()

        logger.info("Tüm veriler başarıyla yüklendi!")
        
    except Exception as e:
        logger.error(f"Genel bir hata oluştu: {str(e)}")
        raise

if __name__ == "__main__":
    upload_data_to_qdrant() 