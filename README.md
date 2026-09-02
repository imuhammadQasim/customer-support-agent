# customer-support-agent

A small **FastAPI + LangChain** chat API, kept intentionally simple so the focus
stays on learning LangChain. No database, no Redis, no background workers — just a
chat endpoint, in-memory conversation history, and a LangChain `ChatAnthropic`
call you can grow into chains, tools, retrieval, agents, etc.

## Requirements

- Python **3.12+**
- An Anthropic API key (`LLM__ANTHROPIC_API_KEY`)

## Setup

```bash
py -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate elsewhere
pip install -r requirements-dev.txt

copy .env.example .env            # Windows;  cp .env.example .env  elsewhere
# edit .env and set LLM__ANTHROPIC_API_KEY

uvicorn app.main:app --reload     # http://127.0.0.1:8000/docs
```

## Try it

```bash
# 1. create a session
curl -X POST http://127.0.0.1:8000/api/v1/sessions

# 2. chat (use the id from step 1)
curl -X POST http://127.0.0.1:8000/api/v1/chat/<session_id> \
  -H "content-type: application/json" \
  -d '{"message": "My order hasn'\''t arrived, what should I do?"}'

# 3. see the stored history
curl http://127.0.0.1:8000/api/v1/sessions/<session_id>/messages
```

Interactive docs: <http://127.0.0.1:8000/docs>

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Liveness |
| POST | `/api/v1/sessions` | Create a session |
| GET | `/api/v1/sessions` | List sessions |
| GET | `/api/v1/sessions/{id}` | Read a session |
| GET | `/api/v1/sessions/{id}/messages` | List a session's messages |
| DELETE | `/api/v1/sessions/{id}` | Delete a session |
| POST | `/api/v1/chat/{session_id}` | Send a message, get a reply |

Every error response uses one shape:
`{"error": {"code", "message", "details", "request_id"}}`.

## Layout

```
app/
  main.py                     FastAPI app factory
  core/
    config.py                 settings (pydantic-settings, reads .env)
    logging.py                structlog console logging + request-id middleware
    exceptions.py             AppError types + JSON error envelope
  api/
    deps.py                   dependency wiring
    v1/router.py              route aggregation
    v1/routes/                health.py  sessions.py  chat.py
  schemas/                    chat.py  session.py       (Pydantic request/response)
  services/
    session_store.py          in-memory conversation store  <-- swap for a DB later
    chat_service.py           LangChain ChatAnthropic call  <-- your LangChain code
  utils/                      ids.py  time.py
```

## Where to build next

- **`app/services/chat_service.py`** — replace the single `ainvoke` call with a
  prompt template, an LCEL chain, retrieval, or a tool-calling agent.
- **`app/services/session_store.py`** — when you outgrow in-memory, swap this for a
  real database (SQLAlchemy, etc.) keeping the same method names.
- Add routes under `app/api/v1/routes/` and register them in `app/api/v1/router.py`.
