import os
import glob
import re
import uuid
import csv

from typing import List
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from fastapi import FastAPI, Request
from pydantic import BaseModel

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

# Find the lowest level of title in a markdown file
def find_markdown_file_depth(filepath: str) -> int:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    depth = 0
    for line in lines:
        if line.startswith("#"):
            current_depth = line.count("#")
            if current_depth > depth:
                depth = current_depth
    return depth

def chunk_markdown_file(filepath: str) -> List[str]:
    max_depth = find_markdown_file_depth(filepath)
    # The split is performed at the level above the deepest header found (e.g., if max is 3, we split at level 2,
    # but if 1, we split at level 1)
    split_level = max(1, min(max_depth, 3) - 1)
    header_pattern = re.compile(rf"^({'#' * split_level})\s+(.+)$")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chunks = []
    current_chunk_lines = []
    current_header = ""

    for line in lines:
        line = line.rstrip()
        if header_pattern.match(line):
            # New header at desired level
            if current_chunk_lines:
                # Save the current chunk
                chunks.append(current_header + "\n\n" + "\n".join(current_chunk_lines).strip())
                current_chunk_lines = []
            current_header = line
        else:
            # Regular line, add to current chunk
            current_chunk_lines.append(line)

    # Add last chunk
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
            print(f"Processing markdown file: {filepath}")
            chunks = chunk_markdown_file(filepath)
        case _ :
            print(f"Unsupported file type: {ext} for file {filepath}")
            return
    print(f"Generated chunks : {chunks[:3]}... Total: {len(chunks)}")
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

# ====== FastAPI Setup ===== #

app = FastAPI()

class EmbedRequest(BaseModel):
    texts: List[str]


class EmbedResponse(BaseModel):
    vectors: List[List[float]]

class IngestRequest(BaseModel):
    qdrant_url: str = "http://localhost:6333"
    corpus: str = "corpus"

class IngestResponse(BaseModel):
    done : bool = False

class CleanRequest(BaseModel):
    qdrant_url: str = "http://localhost:6333"

class CleanResponse(BaseModel):
    done : bool = False

@app.post("/embed", response_model=EmbedResponse)
def embed_texts(request: EmbedRequest):
    vectors = model.encode(request.texts).tolist()
    return {"vectors": vectors}

@app.post("/corpus/ingest", response_model=IngestResponse)
def ingest_files(request: IngestRequest):
    global qdrant
    qdrant = QdrantClient(url=request.qdrant_url)
    print("Starting the ingestion process...")
    ensure_collection()
    pathname = request.corpus+ "/**/*"
    for filepath in glob.glob(pathname, recursive=True):
        if os.path.isfile(filepath):
            process_file(filepath)
    return {"done": True}

@app.post("/corpus/clean", response_model=CleanResponse)
def clean_corpus(request: CleanRequest):
    global qdrant
    qdrant = QdrantClient(url=request.qdrant_url)
    print(f"Cleaning collection: {collection_name}")
    qdrant.delete_collection(collection_name=collection_name)
    ensure_collection()
    return {"done": True}

@app.get("/ready")
def ready():
    is_ready = os.getenv("IS_READY", "false").lower() == "true"
    return {"status": is_ready}