# agentic-platform

Domain-agnostic, production-grade **FastAPI** skeleton for a scalable agentic AI platform.
Skeleton only: correct imports, full type hints, docstrings, and `# TODO:` markers where
real logic goes. It imports and runs, and the test suite is green.

The only example content is a generic **`echo` agent** + **`sample_tool`**, present purely to
demonstrate the pattern. No business use case is hardcoded.

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
| LLM | `app/llm` | Provider-agnostic `LLMProvider` protocol + tier router. |
| Integrations | `app/integrations` | Outbound third-party clients. |
| Core | `app/core` | Config, logging, security, errors, lifespan. |

## Quickstart

```bash
uv sync                       # install (uses pyproject.toml)
cp .env.example .env          # set LLM__ANTHROPIC_API_KEY for real LLM calls
make run                      # uvicorn app.main:app --reload
make test                     # pytest
make lint typecheck           # ruff + mypy
```

Docker:

```bash
make docker-up                # api + postgres + redis
```

Migrations (after you create the first revision):

```bash
make revision m="init"
make upgrade
```

## Key endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Liveness |
| GET | `/api/v1/health/ready` | DB + Redis readiness |
| POST | `/api/v1/sessions` | Create a session |
| GET | `/api/v1/sessions/{id}` | Read a session |
| GET | `/api/v1/sessions/{id}/messages` | List messages |
| DELETE | `/api/v1/sessions/{id}` | Delete a session |
| POST | `/api/v1/chat/{session_id}/stream` | SSE stream of `AgentEvent`s |

`AgentEvent` is a discriminated union: `token`, `tool_call`, `tool_result`, `error`, `done`.

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
