# Compliance Corpus Ingestor

This project provides a simple ingestion script that reads compliance-related documents (policies, RFP responses, etc.), chunks them into paragraphs or rows, generates sentence embeddings, and stores them in a [Qdrant](https://qdrant.tech/) vector database for later to help fill out compliance questionnaires.

---

## 📂 Supported File Types

- `.md`, `.txt` — Chunked by paragraphs
- `.csv` — Chunked by rows

Each chunk is embedded using [all-MiniLM-L6-v2](https://www.sbert.net/docs/pretrained_models.html) and stored in Qdrant with metadata like:
- `text`
- `source` (filename)
- `extension` (`.md`, `.csv`)
- `category` (`policies`, `rfp_responses`, `documents`)

---

## 🚀 Quickstart

### 1. Start Qdrant via Docker

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Put the documents in a corpus/ directory

Create a directory structure like this:

```
corpus/
├── policies/
│   └── access_control.md
├── rfp_responses/
│   └── customer_x.csv
└── documents/
```

### 4. Run the Ingestor

```bash
python ingestor.py
```