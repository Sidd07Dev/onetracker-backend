# ingest.py – production-ready version

import httpx
import asyncio
import os
import uuid
from dotenv import load_dotenv
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --------------------------------------------------
# Load Environment Variables
# --------------------------------------------------
load_dotenv()

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
VECTORIZE_INDEX = os.getenv("VECTORIZE_INDEX_NAME", "onetracker-knowledge")

# 384 dimensions model
EMBEDDING_MODEL = "@cf/baai/bge-small-en-v1.5"

if not CF_ACCOUNT_ID or not CF_API_TOKEN:
    raise ValueError("❌ Missing CF_ACCOUNT_ID or CF_API_TOKEN in .env")

CF_BASE = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"

CF_HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --------------------------------------------------
# Embedding Function
# --------------------------------------------------
async def embed_batch(texts: List[str]) -> List[List[float]]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CF_BASE}/ai/run/{EMBEDDING_MODEL}",
            headers=CF_HEADERS,
            json={"text": texts},
            timeout=60.0
        )

        if resp.status_code != 200:
            print("❌ Embedding Error:", resp.text)
            resp.raise_for_status()

        data = resp.json()

        if "result" not in data or "data" not in data["result"]:
            raise ValueError(f"Embedding failed: {data}")

        embeddings = data["result"]["data"]

        # Validate dimension
        if embeddings:
            print("Embedding dimension:", len(embeddings[0]))

        return embeddings


# --------------------------------------------------
# Ingestion Function
# --------------------------------------------------
async def ingest_docs(
    docs: List[Dict],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    batch_size: int = 40
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    all_vectors = []

    for doc in docs:
        source = doc.get("source", "unknown")
        category = doc.get("category", "")
        title = doc.get("title", source)

        chunks = splitter.split_text(doc["text"])
        print(f"→ {source}: split into {len(chunks)} chunks")

        # Embed chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch_texts = chunks[i:i + batch_size]
            embeddings = await embed_batch(batch_texts)

            for j, emb in enumerate(embeddings):
                chunk_text = batch_texts[j]

                if not isinstance(emb, list):
                    raise ValueError("Embedding is not a list of floats")

                vector_id = f"{source}-{uuid.uuid4().hex[:8]}"

                all_vectors.append({
                    "id": vector_id,
                    "values": emb,
                    "metadata": {
                        "text": chunk_text,
                        "source": source,
                        "title": title,
                        "category": category,
                        "chunk_index": i + j,
                    }
                })

    print(f"\nTotal vectors prepared: {len(all_vectors)}")

    # --------------------------------------------------
    # Upsert into Cloudflare Vectorize
    # --------------------------------------------------
    async with httpx.AsyncClient() as client:
        for k in range(0, len(all_vectors), batch_size):
            batch = all_vectors[k:k + batch_size]

            payload = {
                "vectors": batch   # 🔥 THIS WAS YOUR ISSUE
            }

            url = f"{CF_BASE}/vectorize/v2/indexes/{VECTORIZE_INDEX}/upsert"

            resp = await client.post(
                url,
                headers=CF_HEADERS,
                json=payload,
                timeout=90.0
            )

            if resp.status_code != 200:
                print("❌ Upsert Error:", resp.text)
                resp.raise_for_status()

            result = resp.json()
            print(f"✅ Upserted batch {k // batch_size + 1}: {result}")

    print(f"\n🎉 Total vectors ingested successfully: {len(all_vectors)}")


# --------------------------------------------------
# Load Markdown Docs
# --------------------------------------------------
def load_docs_from_folder(folder="docs"):
    docs = []

    if not os.path.exists(folder):
        raise ValueError(f"Folder '{folder}' does not exist")

    for filename in os.listdir(folder):
        if filename.endswith(".md"):
            path = os.path.join(folder, filename)

            with open(path, "r", encoding="utf-8") as f:
                docs.append({
                    "text": f.read(),
                    "source": filename,
                    "title": filename.replace(".md", "").replace("-", " ").title(),
                    "category": "general"
                })

    return docs


# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    documents = load_docs_from_folder()
    asyncio.run(ingest_docs(documents))
