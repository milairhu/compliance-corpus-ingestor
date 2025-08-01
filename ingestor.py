import argparse
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


def chunk_markdown_file(filepath: str) -> List[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chunks = []
    current_chunk_lines = []
    current_header = ""

    for line in lines:
        line = line.strip()

        if line.startswith("#"):
            # If we hit a new header, flush the current chunk
            if current_chunk_lines:
                chunks.append(current_header + "\n\n" + "\n".join(current_chunk_lines).strip())
                current_chunk_lines = []
            current_header = line  # Save current header
        elif line == "":
            # Blank line: treat as paragraph separator
            if current_chunk_lines and current_chunk_lines[-1] != "":
                current_chunk_lines.append("")  # Force paragraph break
        else:
            current_chunk_lines.append(line)

    # Don't forget the last chunk
    if current_chunk_lines:
        chunks.append(current_header + "\n\n" + "\n".join(current_chunk_lines).strip())

    return [chunk.strip() for chunk in chunks if chunk.strip()]



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
    match ext:
        case ".txt":
            chunks = chunk_text_file(filepath)
        case ".csv":
            chunks = chunk_csv_file(filepath)
        case ".md":
            chunks = chunk_markdown_file(filepath)
        case _ :
            print(f"Unsupported file type: {ext} for file {filepath}")
            return

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
    parser = argparse.ArgumentParser(description="Ingest files into Qdrant")
    parser.add_argument("--qdrant-url", type=str, default="http://localhost:6333", help="URL of the Qdrant instance")
    parser.add_argument("--corpus", type=str, default="corpus", help="Directory containing the corpus files")
    args = parser.parse_args()

    global qdrant
    qdrant = QdrantClient(url=args.qdrant_url)

    print("Starting the ingestion process...")
    ensure_collection()
    pathname = args.corpus+ "/**/*"
    for filepath in glob.glob(pathname, recursive=True):
        if os.path.isfile(filepath):
            process_file(filepath)


if __name__ == "__main__":
    main()
