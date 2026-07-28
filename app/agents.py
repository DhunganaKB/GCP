"""Parallel multi-agent support-ticket triage, built on Google ADK.

Topology
--------

                    ┌─────────────────────────────┐
    ticket text ──▶ │   root  (SequentialAgent)    │
                    │                              │
                    │  1) fan_out (ParallelAgent)  │   <-- runs concurrently
                    │       ├─ sentiment_agent     │
                    │       ├─ category_agent      │
                    │       ├─ priority_agent      │
                    │       └─ reply_agent         │
                    │                              │
                    │  2) router  (LlmAgent)       │   <-- synthesizes results
                    └─────────────────────────────┘

The four worker agents are fully independent: each looks only at the raw ticket
and writes its own slice of the answer into shared session state via `output_key`.
Because they don't depend on one another, ADK's `ParallelAgent` executes them
concurrently. The `router` agent then reads all four state keys and merges them
into one structured triage decision.
"""

import os

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

MODEL = os.getenv("TRIAGE_MODEL", "gemini-2.5-flash")

# --------------------------------------------------------------------------- #
# Independent worker agents (run in parallel)
# --------------------------------------------------------------------------- #

sentiment_agent = LlmAgent(
    name="sentiment_agent",
    model=MODEL,
    description="Judges the customer's emotional tone.",
    instruction=(
        "You are a customer-sentiment analyst. Read the support ticket below and "
        "assess the customer's emotional tone.\n\n"
        "TICKET:\n{ticket_text}\n\n"
        "Respond with ONLY a compact JSON object, no prose, no code fences:\n"
        '{"sentiment": "positive|neutral|negative|angry", '
        '"confidence": 0.0-1.0, "evidence": "<short phrase quoted from the ticket>"}'
    ),
    output_key="sentiment_result",
)

category_agent = LlmAgent(
    name="category_agent",
    model=MODEL,
    description="Classifies the ticket into a support category.",
    instruction=(
        "You are a ticket classifier. Assign the support ticket below to exactly "
        "one category from: Billing, Technical, How-To, Feature-Request, Outage, "
        "Account, Other.\n\n"
        "TICKET:\n{ticket_text}\n\n"
        "Respond with ONLY a compact JSON object, no prose, no code fences:\n"
        '{"category": "<one category>", "subtopic": "<3-6 words>", '
        '"confidence": 0.0-1.0}'
    ),
    output_key="category_result",
)

priority_agent = LlmAgent(
    name="priority_agent",
    model=MODEL,
    description="Scores urgency / priority.",
    instruction=(
        "You are a triage prioritization engine. Score the urgency of the support "
        "ticket below. Consider business impact, blast radius, and money/legal risk. "
        "P1 = critical/outage/revenue-impacting, P2 = high, P3 = normal, P4 = low.\n\n"
        "TICKET:\n{ticket_text}\n\n"
        "Respond with ONLY a compact JSON object, no prose, no code fences:\n"
        '{"priority": "P1|P2|P3|P4", "sla_hours": <int>, '
        '"reason": "<one sentence>"}'
    ),
    output_key="priority_result",
)

reply_agent = LlmAgent(
    name="reply_agent",
    model=MODEL,
    description="Drafts a first-response reply to the customer.",
    instruction=(
        "You are a senior support agent. Draft a warm, professional first-response "
        "reply to the customer ticket below. Acknowledge the issue, state the next "
        "step, and set an expectation. Keep it under 90 words. Do NOT invent "
        "specific refund amounts, dates, or promises you cannot keep.\n\n"
        "TICKET:\n{ticket_text}\n\n"
        "Respond with ONLY a compact JSON object, no prose, no code fences:\n"
        '{"draft_reply": "<the reply text>"}'
    ),
    output_key="reply_result",
)

# --------------------------------------------------------------------------- #
# Fan-out: run the four independent workers concurrently
# --------------------------------------------------------------------------- #

fan_out = ParallelAgent(
    name="fan_out",
    sub_agents=[sentiment_agent, category_agent, priority_agent, reply_agent],
    description="Runs the four independent analysis agents in parallel.",
)

# --------------------------------------------------------------------------- #
# Router: synthesize the parallel results into one triage decision
# --------------------------------------------------------------------------- #

router = LlmAgent(
    name="router",
    model=MODEL,
    description="Merges the parallel results into a final triage decision.",
    instruction=(
        "You are the triage router. Four specialist agents have analyzed a support "
        "ticket in parallel. Their raw JSON outputs are below.\n\n"
        "SENTIMENT: {sentiment_result}\n"
        "CATEGORY: {category_result}\n"
        "PRIORITY: {priority_result}\n"
        "REPLY: {reply_result}\n\n"
        "Merge them into ONE final triage decision. Pick the routing queue from the "
        "category, choose an owner team, and if sentiment is angry/negative AND "
        "priority is P1/P2, set escalate=true.\n\n"
        "Respond with ONLY a compact JSON object, no prose, no code fences:\n"
        '{"category": "...", "priority": "...", "sentiment": "...", '
        '"route_to": "<team/queue>", "escalate": true|false, '
        '"sla_hours": <int>, "suggested_reply": "<the draft reply text>", '
        '"summary": "<one-sentence triage summary>"}'
    ),
    output_key="triage_decision",
)

# --------------------------------------------------------------------------- #
# Root: parallel fan-out, then synthesis
# --------------------------------------------------------------------------- #

root_agent = SequentialAgent(
    name="triage_root",
    sub_agents=[fan_out, router],
    description="Support-ticket triage: parallel analysis then routed decision.",
)
