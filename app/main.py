"""FastAPI service exposing the parallel multi-agent triage pipeline.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, model_validator

# Load GOOGLE_API_KEY from .env BEFORE the ADK/genai clients initialize.
load_dotenv()
# Use the Google AI Studio API key (not Vertex AI) unless told otherwise.
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

from .data import get_ticket, list_tickets  # noqa: E402
from .runner import run_triage  # noqa: E402

app = FastAPI(
    title="Parallel Multi-Agent Support Triage",
    description=(
        "A router agent fans a support ticket out to four independent worker "
        "agents (sentiment, category, priority, reply) that run in parallel via "
        "Google ADK's ParallelAgent, then synthesizes one triage decision."
    ),
    version="1.0.0",
)


class TriageRequest(BaseModel):
    ticket_id: str | None = None
    ticket_text: str | None = None

    @model_validator(mode="after")
    def _one_of(self):
        if not self.ticket_id and not (self.ticket_text and self.ticket_text.strip()):
            raise ValueError("Provide either 'ticket_id' or non-empty 'ticket_text'.")
        return self


@app.get("/")
def root():
    return {
        "service": "parallel-multiagent-triage",
        "framework": "google-adk",
        "model": os.getenv("TRIAGE_MODEL", "gemini-2.5-flash"),
        "endpoints": {
            "GET /tickets": "list synthetic sample tickets",
            "POST /triage": "run triage on a ticket_id or ticket_text",
        },
    }


@app.get("/tickets")
def tickets():
    return {"tickets": list_tickets()}


@app.post("/triage")
async def triage(req: TriageRequest):
    if req.ticket_id:
        ticket = get_ticket(req.ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Unknown ticket_id {req.ticket_id!r}")
        ticket_text = f"Subject: {ticket['subject']}\n\n{ticket['body']}"
        source = {"ticket_id": ticket["id"], "customer": ticket["customer"]}
    else:
        ticket_text = req.ticket_text.strip()
        source = {"ticket_id": None, "customer": None}

    started = time.perf_counter()
    result = await run_triage(ticket_text)
    elapsed_ms = round((time.perf_counter() - started) * 1000)

    return {
        "source": source,
        "input": ticket_text,
        "elapsed_ms": elapsed_ms,
        **result,
    }
