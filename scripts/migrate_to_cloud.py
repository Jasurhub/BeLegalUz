# scripts/migrate_to_cloud.py
"""
Ma'lumotlarni lokal Qdrant'dan Qdrant Cloud'ga ko'chirish
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from source.utils.config import load_config, get_settings


async def migrate_data():
    """Lokal Qdrant'dan Cloud'ga ma'lumotlarni ko'chirish"""
    load_config()
    settings = get_settings()

    print("=" * 60)
    print("🚀 BeLagel: Qdrant Cloud Migratsiyasi")
    print("=" * 60)

    # ✅ Tuzatish: qdrant_collection_name ishlatiladi
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

    # Kollektsiya mavjudligini tekshirish
    print(f"\n🔍 Lokal kolleksiya tekshirilmoqda: {collection_name}")
    try:
        collections = local_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            print(f"❌ Xato: '{collection_name}' kolleksiya lokal Qdrant'da mavjud emas!")
            print(f"   Mavjud kolleksiyalar: {collection_names}")
            return

        print(f"✅ Kolleksiya topildi!")
    except Exception as e:
        print(f"❌ Lokal Qdrant'ga ulanishda xato: {e}")
        return

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

    # Cloud'da kolleksiya mavjudligini tekshirish
    print(f"\n🔍 Cloud'da kolleksiya tekshirilmoqda...")
    try:
        cloud_collections = cloud_client.get_collections().collections
        cloud_collection_names = [c.name for c in cloud_collections]

        if collection_name not in cloud_collection_names:
            print(f"⚠️  Cloud'da '{collection_name}' kolleksiya yo'q. Yaratilmoqda...")

            # Kolleksiya yaratish (lokal bilan bir xil parametrlar)
            local_info = local_client.get_collection(collection_name)

            cloud_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=local_info.config.params.vectors.size,
                    distance=local_info.config.params.vectors.distance,
                )
            )
            print(f"✅ Kolleksiya yaratildi!")
        else:
            print(f"✅ Kolleksiya mavjud!")
    except Exception as e:
        print(f"❌ Cloud kolleksiyani tekshirishda xato: {e}")
        return

    # Cloud'ga yuklash
    print(f"\n☁️  Cloud'ga yuklanmoqda...")
    batch_size = 100
    total_batches = (len(local_points) + batch_size - 1) // batch_size

    for i in range(0, len(local_points), batch_size):
        batch = local_points[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        try:
            cloud_client.upsert(
                collection_name=collection_name,
                points=batch
            )
            progress = min(i + batch_size, len(local_points))
            percentage = (progress / len(local_points)) * 100
            print(f"   ✅ Batch {batch_num}/{total_batches} ({percentage:.1f}%) - {progress}/{len(local_points)} points")
        except Exception as e:
            print(f"   ❌ Batch {batch_num} yuklashda xato: {e}")
            continue

    # Yakuniy tekshiruv
    print(f"\n🔍 Cloud'dagi ma'lumotlar tekshirilmoqda...")
    try:
        cloud_info = cloud_client.get_collection(collection_name)
        print(f"✅ Cloud'da {cloud_info.points_count} ta point mavjud")
    except Exception as e:
        print(f"⚠️  Cloud kolleksiya ma'lumotlarini olishda xato: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 Migratsiya tugadi!")
    print(f"   📊 Jami {len(local_points)} ta point cloud'ga yuklandi")
    print("=" * 60)

    # Klientlarni yopish
    local_client.close()
    cloud_client.close()


if __name__ == "__main__":
    asyncio.run(migrate_data())