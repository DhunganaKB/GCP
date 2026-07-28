# Parallel Multi-Agent Support Triage (Google ADK + FastAPI)

A **router agent** fans one support ticket out to **four independent worker agents**
that run **concurrently** (Google ADK `ParallelAgent`), then synthesizes their
outputs into a single routed triage decision. Everything runs on **synthetic
data** — no real business systems required.

## Business scenario

A support desk receives a ticket. Four things must be decided about it, and none
of them depend on each other, so they can all be computed at the same time:

| Worker agent      | Answers                                    |
| ----------------- | ------------------------------------------ |
| `sentiment_agent` | How does the customer feel?                |
| `category_agent`  | What kind of ticket is this?               |
| `priority_agent`  | How urgent is it (P1–P4 + SLA)?            |
| `reply_agent`     | Draft a first-response reply.              |

Because the four tasks are **independent**, the router runs them in parallel and
then merges them: pick a queue, choose an owner team, and escalate if the
customer is angry **and** the priority is high.

```
ticket ─▶ root (SequentialAgent)
             ├─ fan_out (ParallelAgent)   ← 4 agents run concurrently
             │    ├─ sentiment_agent
             │    ├─ category_agent
             │    ├─ priority_agent
             │    └─ reply_agent
             └─ router (LlmAgent)          ← merges into one decision
```

## Layout

```
app/
  data.py     # synthetic sample tickets (TCK-1001 … TCK-1004)
  agents.py   # the ADK agent tree (workers, ParallelAgent, router)
  runner.py   # async wrapper that drives the tree and returns state
  main.py     # FastAPI app
.env          # GOOGLE_API_KEY=...
requirements.txt
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`.env` must contain a Google AI Studio key:

```
GOOGLE_API_KEY=your_key_here
```

Optional override: `TRIAGE_MODEL=gemini-2.5-flash` (the default).

## Run

```bash
.venv/bin/uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive Swagger UI.

## Endpoints

| Method | Path       | Purpose                                              |
| ------ | ---------- | ---------------------------------------------------- |
| GET    | `/`        | Service info                                         |
| GET    | `/tickets` | List the synthetic sample tickets                    |
| POST   | `/triage`  | Triage a ticket by `ticket_id` **or** `ticket_text`  |

### Examples

```bash
# Triage a bundled synthetic ticket
curl -X POST http://127.0.0.1:8000/triage \
  -H 'Content-Type: application/json' \
  -d '{"ticket_id":"TCK-1003"}'

# Triage arbitrary free text
curl -X POST http://127.0.0.1:8000/triage \
  -H 'Content-Type: application/json' \
  -d '{"ticket_text":"I was double charged $99 and I am really upset, refund now."}'
```

### Sample response (trimmed)

```json
{
  "elapsed_ms": 5400,
  "workers": {
    "sentiment": {"sentiment": "angry", "confidence": 1.0},
    "category":  {"category": "Outage"},
    "priority":  {"priority": "P1", "sla_hours": 0.5},
    "reply":     {"draft_reply": "..."}
  },
  "decision": {
    "priority": "P1",
    "route_to": "SRE/DevOps",
    "escalate": true,
    "summary": "P1 production outage on /v2/payments ..."
  }
}
```

## Where the parallelism is

`app/agents.py` → `fan_out = ParallelAgent(sub_agents=[...])`. ADK executes those
four sub-agents concurrently and each writes to its own `output_key` in shared
session state. The `router` agent reads all four keys via `{...}` template
placeholders and produces the final decision.
