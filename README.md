# Compliance Corpus Ingestor API

This project exposes an API for:
- Ingesting compliance documents (policies, RFPs, etc.) into Qdrant.
- Cleaning the Qdrant database
- On-the-fly text vectorization

---

## Launch Qdrant

```
docker run -p 6333:6333 -p 6334:6334 \
-v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
qdrant/qdrant
```


## 🚦 API Endpoints

- **POST `/embed`**  
  Returns the vectorized (embedding) version of an input string.

- **POST `/corpus/ingest`**  
  Triggers ingestion of the policy corpus into Qdrant.

- **POST `/corpus/clean`**  
    Empties the Qdrant database.
---

## 📂 Corpus Organization

Place your documents in `/app/corpus` with the following structure:

```
/app/corpus/ 
      ├── policies/ 
             │ 
             └── access_control.md 
      ├── rfp_responses/ 
             │ 
             └── customer_x.csv 
     └── documents/
```

## ▶️ Quickstart

Build and run the API in Docker:

docker build -t ingest-transform-api .
docker run -d  -v ./corpus:app/corpus --name ingest-transform-api -p 8000:8000 ingest-transform-api

## 🧪 Usage

### /embed
Make a POST request to the /embed endpoint:
```
curl -X POST http://localhost:8000/embed \
-H "Content-Type: application/json" \
-d '{"texts": ["What are your data retention policies?"]}'
```

Example response:

{
"vectors": [
[0.123, -0.456, 0.789, ...]  // Vector of floats
]
}

### /corpus/ingest
Trigger ingestion of the corpus.
```
curl -X POST http://localhost:8000/corpus/ingest \
-H "Content-Type: application/json" \
-d '{"qdrant_url": "http://qdrant:6333", "corpus": "/app/corpus"}'
```

### /corpus/clean
Empty the Qdrant database:
```
curl -X POST http://localhost:8000/corpus/clean \
-H "Content-Type: application/json" \
-d '{"qdrant_url": "http://qdrant:6333"}'
```