# scripts/migrate_to_cloud.py
"""
Ma'lumotlarni lokal Qdrant'dan Qdrant Cloud'ga ko'chirish
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from source.utils.config import load_config, get_settings


async def migrate_data():
    """Lokal Qdrant'dan Cloud'ga ma'lumotlarni ko'chirish"""
    load_config()
    settings = get_settings()

    print("=" * 60)
    print("🚀 BeLagel: Qdrant Cloud Migratsiyasi")
    print("=" * 60)

    collection_name = settings.qdrant_collection_name
    print(f"📦 Kolleksiya nomi: {collection_name}")
    print(f"🌐 Cloud URL: {settings.qdrant_url}")
    print()

    # Lokal Qdrant
    print("🔌 Lokal Qdrant'ga ulanmoqda...")
    local_client = QdrantClient(url="http://localhost:6333")

    # Cloud Qdrant
    print("☁️  Qdrant Cloud'ga ulanmoqda...")
    cloud_client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

    # Lokal'dan ma'lumotlarni o'qish
    print("\n📖 Lokal'dan ma'lumotlar o'qilmoqda...")
    try:
        local_points = local_client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=True
        )[0]
    except Exception as e:
        print(f"❌ Ma'lumotlarni o'qishda xato: {e}")
        return

    if not local_points:
        print("⚠️  Lokal Qdrant'da hech qanday ma'lumot topilmadi!")
        return

    print(f"✅ {len(local_points)} ta point topildi")

    # Cloud'da kolleksiya yaratish (an'anaviy usul bilan)
    print(f"\n🔍 Cloud'da kolleksiya yaratilmoqda...")
    try:
        # Kolleksiyani aniq parametrlar bilan yaratish
        cloud_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1024,  # multilingual-e5-large o'lchami
                distance=Distance.COSINE,
            ),
            shard_number=2  # Cloud uchun optimal
        )
        print(f"✅ Kolleksiya yaratildi!")
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower() or "already" in error_msg.lower():
            print(f"✅ Kolleksiya allaqachon mavjud!")
        else:
            print(f"❌ Kolleksiya yaratishda xato: {e}")
            return

    # Cloud'ga yuklash
    print(f"\n☁️  Cloud'ga yuklanmoqda...")
    batch_size = 100
    total_batches = (len(local_points) + batch_size - 1) // batch_size
    success_count = 0

    for i in range(0, len(local_points), batch_size):
        batch = local_points[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        try:
            # Point'larni aniq formatda tayyorlash
            points = []
            for point in batch:
                points.append(PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload
                ))

            cloud_client.upsert(
                collection_name=collection_name,
                points=points
            )
            success_count += len(batch)
            progress = min(i + batch_size, len(local_points))
            percentage = (progress / len(local_points)) * 100
            print(f"   ✅ Batch {batch_num}/{total_batches} ({percentage:.1f}%) - {progress}/{len(local_points)} points")
        except Exception as e:
            print(f"   ❌ Batch {batch_num} yuklashda xato: {e}")
            continue

    print("\n" + "=" * 60)
    print(f"🎉 Migratsiya tugadi!")
    print(f"   📊 Jami {success_count}/{len(local_points)} ta point cloud'ga yuklandi")
    print("=" * 60)

    # Klientlarni yopish
    local_client.close()
    cloud_client.close()


if __name__ == "__main__":
    asyncio.run(migrate_data())