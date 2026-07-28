"""Synthetic support tickets.

No real business data is used anywhere in this project. These records stand in
for what would normally come from a helpdesk system (Zendesk, Freshdesk, etc.).
The FastAPI layer can either accept an ad-hoc ticket body or pull one of these
synthetic tickets by id, so the whole pipeline is runnable with zero setup.
"""

from typing import Optional

# A small, deliberately varied set so you can see the parallel agents disagree
# on sentiment / priority / category across different inputs.
SYNTHETIC_TICKETS: dict[str, dict] = {
    "TCK-1001": {
        "id": "TCK-1001",
        "customer": "Acme Logistics",
        "channel": "email",
        "subject": "Charged twice for the same invoice",
        "body": (
            "This is the THIRD time I'm writing. We were billed $4,200 twice on "
            "invoice #88231 and nobody has refunded us. Our finance team is "
            "furious and we are considering cancelling our contract. Fix this today."
        ),
    },
    "TCK-1002": {
        "id": "TCK-1002",
        "customer": "Jane Individual",
        "channel": "chat",
        "subject": "How do I export my report to PDF?",
        "body": (
            "Hi! Loving the product so far. Quick question - I can see the report "
            "on screen but I can't figure out how to download it as a PDF. Is that "
            "possible? No rush, thanks!"
        ),
    },
    "TCK-1003": {
        "id": "TCK-1003",
        "customer": "Northwind Bank",
        "channel": "phone-transcript",
        "subject": "API returning 500 errors in production",
        "body": (
            "Our production integration started returning HTTP 500 from the "
            "/v2/payments endpoint about 40 minutes ago. Roughly 30% of our "
            "customer transactions are failing right now. This is business critical. "
            "We need someone on this immediately."
        ),
    },
    "TCK-1004": {
        "id": "TCK-1004",
        "customer": "Bright Studio",
        "channel": "email",
        "subject": "Feature request: dark mode",
        "body": (
            "Would be great to have a dark mode in the dashboard. Our designers "
            "work late and the white background is hard on the eyes. Not urgent, "
            "just a nice-to-have for a future release."
        ),
    },
}


def get_ticket(ticket_id: str) -> Optional[dict]:
    return SYNTHETIC_TICKETS.get(ticket_id)


def list_tickets() -> list[dict]:
    return list(SYNTHETIC_TICKETS.values())
