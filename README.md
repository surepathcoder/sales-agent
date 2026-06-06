# Kijani AI

Agentic AI sales platform for Tanzanian B2B businesses. Autonomous agents discover leads, research accounts, and engage via WhatsApp-first outreach with Swahili-English support.

## Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Frontend | Next.js 14+ App Router, TanStack Query, shadcn/ui |
| Database | PostgreSQL 15 + pgvector |
| Cache/Queue | Redis 7 |
| Agents | LangGraph, LangChain |
| LLM | Groq API (Llama 3.1) |
| Messaging | WhatsApp Web.js (separate Node service) |
| Payments | M-Pesa (mock MVP) |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (local frontend dev)
- Python 3.11+ (local backend dev)
- Groq API key

### 1. Clone and configure

```bash
cd kijani-ai
cp backend/.env.example backend/.env
# Edit backend/.env with your GROQ_API_KEY and SECRET_KEY
```

### 2. Start with Docker

```bash
docker compose up -d
```

Services:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs (dev): http://localhost:8000/docs
- WhatsApp service: http://localhost:8001

### 3. Run migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Local development (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Multi-Tenant Architecture

- Row-level isolation via `tenant_id` on every tenant-scoped table.
- JWT contains `user_id`, `tenant_id`, `role`.
- `TenantContextMiddleware` extracts tenant from JWT into request state.
- All service-layer queries filter by `tenant_id`.

## Agent Pipeline

```
Scout → Researcher → Outreach → Closer
```

- **Scout**: Google Maps, BRELA, Facebook, Instagram, web scraping
- **Researcher**: Account intelligence, decision-makers, buying signals
- **Outreach**: WhatsApp/email with Swahili-English generation (Groq)
- **Closer**: Deal stage management, forecasting

## Project Structure

See `.cursorrules` and the spec in the repository root for the full layout.

## License

Proprietary — Kijani AI
"# sales-agent" 
