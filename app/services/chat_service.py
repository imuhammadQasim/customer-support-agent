"""Chat use case: run a user message through a LangChain chat model.

This is where your LangChain code goes. Right now it is the smallest thing
that works: build a message list (system prompt + past turns + new message),
call the model, return the reply. Later you can swap ``self._model.ainvoke``
for a chain, an agent, retrieval, tools, etc.
"""

from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.session_store import Session, SessionStore

SYSTEM_PROMPT = (
    "You are a helpful, friendly customer support assistant. "
    "Answer clearly and concisely. If you are unsure, say so."
)


class LLMNotConfiguredError(AppError):
    """No Anthropic API key was provided."""

    status_code = 503
    code = "llm_not_configured"


class LLMCallError(AppError):
    """The model call failed."""

    status_code = 502
    code = "llm_error"


def _history_to_messages(session: Session, new_message: str) -> list[BaseMessage]:
    """Turn stored turns + the new user message into LangChain messages."""
    messages: list[BaseMessage] = [SystemMessage(SYSTEM_PROMPT)]
    for turn in session.messages:
        if turn.role == "user":
            messages.append(HumanMessage(turn.content))
        else:
            messages.append(AIMessage(turn.content))
    messages.append(HumanMessage(new_message))
    return messages


def _text_of(message: AIMessage) -> str:
    """Anthropic replies are usually a plain string; handle block lists too."""
    content = message.content
    if isinstance(content, str):
        return content
    parts = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    return "".join(parts)


class ChatService:
    """Holds the chat model and answers one turn at a time."""

    def __init__(self, *, store: SessionStore, settings: Settings) -> None:
        self._store = store
        self._api_key = settings.llm.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model: ChatAnthropic | None = None
        if self._api_key:
            self._model = ChatAnthropic(
                model=settings.llm.model,
                api_key=self._api_key,
                max_tokens=settings.llm.max_tokens,
                temperature=settings.llm.temperature,
                timeout=settings.llm.timeout_s,
            )

    async def reply(self, *, session_id: str, message: str) -> str:
        """Answer ``message`` in the context of ``session_id`` and store both turns."""
        if self._model is None:
            raise LLMNotConfiguredError(
                "No Anthropic API key configured. Set LLM__ANTHROPIC_API_KEY in your .env file."
            )

        session = self._store.get(session_id)
        lc_messages = _history_to_messages(session, message)

        try:
            ai_message = await self._model.ainvoke(lc_messages)
        except Exception as exc:  # noqa: BLE001 - surface as one clean envelope
            raise LLMCallError(f"Model call failed: {exc}") from exc

        reply_text = _text_of(ai_message)
        self._store.add_message(session_id, role="user", content=message)
        self._store.add_message(session_id, role="assistant", content=reply_text)
        return reply_text
