# agentic-platform (customer-support-agent)

Domain-agnostic, production-grade **FastAPI** skeleton for a scalable agentic AI platform.
This is the base/skeleton for the `customer-supprot-agent` repo — it ships **no** business
logic. Everything is stubbed with correct imports, full type hints, docstrings, and
`# TODO:` markers where real logic goes. It imports and runs as-is.

The only example content is a generic **`echo` agent** + **`sample_tool`**, present purely to
demonstrate the pattern. Nothing domain-specific is hardcoded — build your use case on top.

## Requirements

- Python **3.12+**
- PostgreSQL + Redis (only needed at runtime for DB-backed / memory features; the test
  suite uses in-memory SQLite and a fake Redis)
- An Anthropic API key for real LLM calls (`LLM__ANTHROPIC_API_KEY`)

Dependencies are declared in `pyproject.toml` and mirrored to `requirements.txt` /
`requirements-dev.txt` for plain-pip workflows.

## Quickstart (pip)

```bash
py -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt

copy .env.example .env            # Windows;  cp .env.example .env  elsewhere
# edit .env and set LLM__ANTHROPIC_API_KEY if you want real LLM calls

uvicorn app.main:app --reload     # http://127.0.0.1:8000
pytest                            # run the test suite
ruff check app tests             # lint
mypy app                         # type-check
```

## Quickstart (uv)

```bash
uv sync
cp .env.example .env
make run        # uvicorn app.main:app --reload
make test       # pytest
make lint       # ruff check
make typecheck  # mypy
```

## Docker

```bash
make docker-up                    # api + postgres + redis
# or: docker compose -f docker/docker-compose.yml up --build
```

## Migrations

Alembic is wired for async and reads the DB URL from app settings. No revisions ship with
the skeleton — create the first one once you have models you want to persist:

```bash
make revision m="init"            # uv run alembic revision --autogenerate -m "init"
make upgrade                      # uv run alembic upgrade head
```

## Architecture

Strict one-way dependency direction:

```
routes  ->  services  ->  repositories / agents  ->  db / llm / integrations
```

- No SQL and no LLM calls in route handlers.
- Never import "upward" (e.g. a repository importing a service).

| Layer | Package | Responsibility |
|-------|---------|----------------|
| API | `app/api` | HTTP, validation, SSE. Depends on services only. |
| Services | `app/services` | Use cases; orchestrate repositories + the agent runtime. |
| Repositories | `app/repositories` | All SQL. Generic `BaseRepository[T]` CRUD. |
| Agents | `app/agents` | `BaseAgent`, registry, runtime, tools, memory. |
| LLM | `app/llm` | Provider-agnostic `LLMProvider` protocol + tier router + Anthropic client. |
| Integrations | `app/integrations` | Outbound third-party clients. |
| Core | `app/core` | Config, logging, security, errors, lifespan. |
| Workers | `app/workers` | Off-request agent execution (queue TODO). |

## Project layout

```
app/
  main.py                     FastAPI app factory (create_app / app)
  core/       config.py logging.py security.py exceptions.py lifespan.py
  api/        deps.py  v1/router.py  v1/routes/{health,chat,sessions}.py
  schemas/    common.py chat.py session.py agent_events.py
  models/     base.py session.py message.py            (SQLAlchemy 2.0 async)
  repositories/  base.py session.py message.py         (BaseRepository[T])
  services/   session_service.py chat_service.py
  agents/     base.py registry.py runtime.py echo_agent.py
              prompts/echo.py
              tools/{base,registry,sample_tool}.py     (@register_tool)
              memory/{base,redis_memory}.py            (SessionMemory)
  llm/        base.py router.py anthropic_client.py
  integrations/  base.py example_integration.py
  db/         base.py session.py
  workers/    worker.py tasks.py
  utils/      ids.py sse.py time.py
tests/        conftest.py + mirrors of app/ (async client, transactional DB)
alembic/      env.py (async) script.py.mako versions/
docker/       Dockerfile (multi-stage) docker-compose.yml
```

## Configuration

`pydantic-settings` with nested groups; env vars use a `__` delimiter (see `.env.example`):

| Group | Example var | Notes |
|-------|-------------|-------|
| `app` | `APP__ENV`, `APP__AUTH_DISABLED` | auth is disabled by default in the skeleton |
| `db` | `DB__URL` | `postgresql+asyncpg://...` |
| `redis` | `REDIS__URL`, `REDIS__SESSION_TTL_S` | short-term agent memory |
| `llm` | `LLM__ANTHROPIC_API_KEY`, `LLM__{FAST,BALANCED,DEEP}_MODEL` | tier -> model map |

## Endpoints

Base URL when running locally: `http://127.0.0.1:8000`. Interactive docs at `/docs`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Liveness |
| GET | `/api/v1/health/ready` | DB + Redis readiness |
| POST | `/api/v1/sessions` | Create a session |
| GET | `/api/v1/sessions/{id}` | Read a session |
| GET | `/api/v1/sessions/{id}/messages` | List messages (paginated) |
| DELETE | `/api/v1/sessions/{id}` | Delete a session |
| POST | `/api/v1/chat/{session_id}/stream` | SSE stream of `AgentEvent`s |

`AgentEvent` is a discriminated union: `token`, `tool_call`, `tool_result`, `error`, `done`.
Every error response uses one envelope: `{"error": {"code", "message", "details", "request_id"}}`.

---

## How to extend

### Add a new agent

1. Create `app/agents/my_agent.py`:

   ```python
   from collections.abc import AsyncIterator

   from app.agents.base import BaseAgent
   from app.agents.registry import register_agent
   from app.schemas.agent_events import AgentEvent, DoneEvent, TokenEvent


   @register_agent
   class MyAgent(BaseAgent):
       name = "my_agent"
       description = "What this agent does."

       async def stream(self, user_input: str) -> AsyncIterator[AgentEvent]:
           # TODO: real logic. Use self.context.llm_router / .tools / .history / .memory
           yield TokenEvent(text="...")
           yield DoneEvent(reason="stop")
   ```

2. Import it so registration runs: add a line to `app/agents/__init__.py`:

   ```python
   from app.agents import my_agent as _my_agent  # noqa: F401
   ```

3. Use it by creating a session with `{"agent_name": "my_agent"}` (or pass
   `agent_name` per turn in the chat request).

### Add a new tool

1. Create `app/agents/tools/my_tool.py`:

   ```python
   from pydantic import BaseModel, Field

   from app.agents.tools.base import BaseTool, ToolResult
   from app.agents.tools.registry import register_tool


   class MyToolArgs(BaseModel):
       query: str = Field(..., description="...")


   @register_tool
   class MyTool(BaseTool[MyToolArgs]):
       name = "my_tool"
       description = "What this tool does."
       args_schema = MyToolArgs

       async def execute(self, args: MyToolArgs) -> ToolResult:
           # TODO: real logic
           return ToolResult(ok=True, content=...)
   ```

2. Import it so registration runs: add a line to `app/agents/tools/__init__.py`:

   ```python
   from app.agents.tools import my_tool as _my_tool  # noqa: F401
   ```

   `ToolRegistry.default()` now includes it; `agent.context.tools.get("my_tool")` resolves it.

### Add a new API route

1. Create `app/api/v1/routes/widgets.py`:

   ```python
   from fastapi import APIRouter

   from app.api.deps import SessionServiceDep  # or a new service dep

   router = APIRouter(prefix="/widgets", tags=["widgets"])


   @router.get("")
   async def list_widgets(service: SessionServiceDep) -> dict:
       # TODO: call a service method; no SQL / LLM here
       return {"items": []}
   ```

2. Register it in `app/api/v1/router.py`:

   ```python
   from app.api.v1.routes import widgets
   v1_router.include_router(widgets.router)
   ```

3. If it needs new behaviour, add a method to a service in `app/services/`,
   backed by a repository in `app/repositories/` — never reach into the DB
   from the route.
