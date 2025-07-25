# Creating a basic project structure with an ingestor.py script
# The script reads .md, .txt, and .csv files from a folder, chunks them, generates embeddings and pushes them to Qdrant

import os
import glob
import uuid
import csv

from typing import List
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance

# ====== Variables ===== #

# Load the sentence transformer model that will be used for embedding (generating vector representations of text)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Qdrant client setup
qdrant = QdrantClient(url="http://localhost:6333")
collection_name = "compliance_corpus"  # Use of only one collection


# ====== Functions ===== #

# Create collection if it doesn't exist
def ensure_collection():
    collections = qdrant.get_collections().collections
    if not any(c.name == collection_name for c in collections):
        print(f"Creating collection: {collection_name}")
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    else:
        print(f"Collection {collection_name} already exists.")


# Read and chunk .txt
def chunk_text_file(filepath: str) -> List[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Split by double newlines for paragraphs
    chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]
    return chunks


# TODO improve chunking for markdown files to handle headers and sections better
def chunk_markdown_file(filepath: str) -> List[str]:
    # Read the markdown and chunk by sections
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Split by headers
    chunks = []
    current_chunk = []
    for line in content.splitlines():
        if line.startswith("#"):
            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())
                current_chunk = []
        current_chunk.append(line)
    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())
    return [chunk for chunk in chunks if chunk.strip()]


# Read and chunk .csv files (each row as a chunk)
def chunk_csv_file(filepath: str) -> List[str]:
    chunks = []
    with open(filepath, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        for row in reader:
            text = ", ".join(f"{h}: {v}" for h, v in zip(headers, row))
            chunks.append(text)
    return chunks


# Embed and insert chunks into Qdrant
def process_file(filepath: str):
    print(f"Processing: {filepath}")

    ext = os.path.splitext(filepath)[1]
    if ext not in [".txt", ".md", ".csv"]:
        print(f"Skipping unsupported file type: {ext} for file {filepath}")
        return

    chunks = []
    if ext in [".txt", ".md"]:
        chunks = chunk_text_file(filepath)
    elif ext == ".csv":
        chunks = chunk_csv_file(filepath)
    category = filepath.split('/')[1] if '/' in filepath else 'documents'

    for chunk in chunks:
        # Generate embedding for the chunk
        embedding = model.encode(chunk).tolist()
        payload = {
            "text": chunk,
            "source": os.path.basename(filepath),
            "extension": ext,
            "category": category,
        }
        # Upsert the chunk into Qdrant
        qdrant.upsert(
            collection_name=collection_name,
            wait=True,
            points=[PointStruct(id=str(uuid.uuid4()), vector=embedding, payload=payload)]
        )


def main():
    print("Starting the ingestion process...")
    ensure_collection()
    for filepath in glob.glob("corpus/**/*", recursive=True):
        if os.path.isfile(filepath):
            process_file(filepath)


if __name__ == "__main__":
    main()
