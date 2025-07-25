# Compliance Corpus Ingestor

This project provides a simple ingestion pipeline that reads compliance-related documents (policies, RFP responses, etc.), chunks them into paragraphs or rows, generates sentence embeddings, and stores them in a [Qdrant](https://qdrant.tech/) vector database for later semantic search via an LLM.

---

## 📂 Supported File Types

- `.md`, `.txt` — Chunked by paragraphs
- `.csv` — Chunked by rows

Each chunk is embedded using [all-MiniLM-L6-v2](https://www.sbert.net/docs/pretrained_models.html) and stored in Qdrant with metadata like:
- `text`
- `source` (filename)
- `extension` (e.g. `.csv`)
- `category` (`policies`, `rfp_responses`, `documents`)

---

## 🚀 Quickstart

### 1. Start Qdrant via Docker

```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
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
└── annex_info.txt
```

### 4. Run the Ingestor

```bash
python ingestor.py
```