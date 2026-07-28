"""Thin async wrapper that drives the ADK agent tree and returns state."""

import json
import re
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agents import root_agent

APP_NAME = "ticket_triage"
USER_ID = "fastapi"

_session_service = InMemorySessionService()
_runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=_session_service,
)


def _parse_json(raw: Any) -> Any:
    """Best-effort parse of an LLM string that should be JSON."""
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    # Strip ```json ... ``` fences if the model added them anyway.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return raw


async def run_triage(ticket_text: str) -> dict:
    """Run the parallel triage pipeline over one ticket, return structured state."""
    session = await _session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={"ticket_text": ticket_text},
    )

    message = types.Content(role="user", parts=[types.Part(text=ticket_text)])

    # Drain the event stream; agents write their results into session state.
    async for _ in _runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        pass

    final = await _session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    state = final.state if final else {}

    return {
        "workers": {
            "sentiment": _parse_json(state.get("sentiment_result")),
            "category": _parse_json(state.get("category_result")),
            "priority": _parse_json(state.get("priority_result")),
            "reply": _parse_json(state.get("reply_result")),
        },
        "decision": _parse_json(state.get("triage_decision")),
    }
