from __future__ import annotations

from google.adk.agents import Agent

from concierge.prompts import MATCHING_AGENT_INSTRUCTION
from concierge.settings import get_settings
from concierge.tools.aimm import match_creators
from concierge.tools.cren import enrich_creator

_settings = get_settings()

matching_agent = Agent(
    name="matching_agent",
    model=_settings.concierge_worker_model,
    description=(
        "Matches the best creators from the CashTime database to a brand "
        "profile and refreshes their contact + audience metrics."
    ),
    instruction=MATCHING_AGENT_INSTRUCTION,
    tools=[match_creators, enrich_creator],
)
