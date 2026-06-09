from __future__ import annotations

from google.adk.agents import Agent

from concierge.prompts import OUTREACH_AGENT_INSTRUCTION
from concierge.settings import get_settings
from concierge.tools.aicrops import draft_outreach, schedule_sequence

_settings = get_settings()

outreach_agent = Agent(
    name="outreach_agent",
    model=_settings.concierge_worker_model,
    description=(
        "Drafts personalised first-touch outreach in the brand tone-of-voice "
        "and schedules a 3-step follow-up sequence per creator. Drafts and "
        "schedules only - never sends."
    ),
    instruction=OUTREACH_AGENT_INSTRUCTION,
    tools=[draft_outreach, schedule_sequence],
)
