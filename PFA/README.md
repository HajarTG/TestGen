# TestGen - AI-Powered Java Test Generator

An end-to-end platform that automatically generates JUnit 5 tests for Java projects using a RAG-augmented GPT pipeline.

## Architecture

```
React Frontend  ->  FastAPI Backend  ->  PostgreSQL
                         |
                    Redis Queue  ->  Celery Worker
                                       |- JavaParser (analysis)
                                       |- Strategy Selector
                                       |- RAG Pipeline (Qdrant + OpenAI Embeddings)
                                       |- GPT-4o (test generation)
                                       `- Validator (javac compile + score)
Qdrant (Vector DB)
Prometheus + Grafana (Monitoring)
```

## Quick Start

### 2. Start all services
Docker builds the backend, frontend, worker, and Java parser artifact automatically.

```bash
docker-compose up --build
```

### 3. Build the Java Parser JAR for local worker development
Only needed when running the Celery worker directly outside Docker.

```bash
cd java-parser
mvn package -DskipTests
cd ..
```

### 4. Open the app
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## Services

| Service | Port | Description |
|---|---|---|
| Frontend (React) | 3000 | Web UI |
| Backend (FastAPI) | 8000 | REST API |
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Job queue |
| Qdrant | 6333 | Vector database |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Dashboards |

## Pipeline Steps

1. **Java Analysis** - JavaParser CLI reads `.java` files, extracts classes/methods/annotations/control-flow into a structured JSON model
2. **Strategy Selection** - Rule-based engine selects test strategy (`http`, `db`, `exception`, `branch`, `unit`) per method
3. **RAG Embedding** - Method code chunks are embedded (OpenAI `text-embedding-3-small`) and stored in Qdrant
4. **Prompt Building + GPT** - Method + RAG context + strategy -> GPT-4o -> JUnit test code
5. **Validation** - `javac` compilation attempt, assertion counting, scoring (0-100)

## Development

### Backend only
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend only
```bash
cd frontend
npm install
npm run dev
```

### Celery worker only
```bash
cd backend
celery -A app.celery_app.celery_config worker --loglevel=info -Q testgen
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key (required) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_HOST` | Qdrant hostname |
| `SECRET_KEY` | JWT signing secret (change in production!) |
