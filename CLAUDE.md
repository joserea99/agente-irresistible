# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project

**Iglesia Irresistible OS** — AI-powered ministerial operating system for Spanish-speaking churches following the Irresistible Church (North Point / Andy Stanley) strategy.

## Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, Radix UI
- **AI:** Google Gemini 2.5 Flash (chat + embeddings via `google-genai`)
- **Database:** Supabase (PostgreSQL + pgvector + Auth)
- **Payments:** Stripe
- **External:** Brandfolder API (asset management)
- **Deployment:** Railway (monorepo: backend + frontend as separate services)

## Verification

### Backend
```bash
cd backend
pip install -r requirements.txt
pytest
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm run lint
```

### Full verification
```bash
./scripts/verify.sh
```

## Repository shape

- `backend/` — FastAPI application
  - `backend/app/routers/` — API endpoints (auth, chat, dojo, brandfolder, knowledge, magic, sync, subscription)
  - `backend/app/services/` — Business logic (chat_service, dojo_service, agent_service, personas, vector_store, rag_service, etc.)
  - `backend/app/models/` — Pydantic request/response models
  - `backend/app/core/` — Config, exceptions, logging
  - `backend/main.py` — FastAPI app setup, CORS, rate limiting, scheduler
- `frontend/` — Next.js application
  - `frontend/app/` — Pages (chat, dojo, knowledge, admin, dashboard, login, register)
  - `frontend/components/` — Shared UI components
  - `frontend/lib/` — Stores, config, i18n, Supabase client
- `irresistible_brain_db/` — Local ChromaDB vector cache (fallback)

## Key conventions

- **Personas** are defined in `backend/app/services/personas.py` as a `PERSONAS` dict. Each key is a director name, each value is a complete system prompt.
- **Directors** are the 10+ AI personas (Pastor Principal, Niños, Estudiantes, Adultos, Media, etc.) that users chat with.
- **RAG** uses Supabase pgvector via RPC `match_documents`. Embeddings generated with Gemini `gemini-embedding-001`.
- **Auth** is Supabase-based. JWT tokens verified server-side. Roles: admin, member, pastor_principal, kids_director, etc.
- **Deployment model** is one instance per church — env vars contain that church's API keys.
- All AI responses must support **Spanish and English** (language detected from user input).
- Configuration lives in `backend/app/core/config.py` (Pydantic BaseSettings from env vars).

## Working agreement

- Keep backend services modular — one service per domain (chat, dojo, knowledge, etc.).
- When adding a new director/persona, update both `personas.py` and `frontend/lib/dashboard-config.tsx`.
- When adding a new router, register it in `backend/main.py`.
- Prefer small, testable changes. Run `pytest` after backend changes.
- Do not commit `.env` files or API keys.
