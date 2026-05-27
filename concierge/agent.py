from __future__ import annotations

from google.adk.agents import Agent

from concierge.prompts import CONCIERGE_SYSTEM_INSTRUCTION
from concierge.settings import get_settings
from concierge.tools import ALL_TOOLS

_settings = get_settings()


root_agent = Agent(
    name="cashtime_brand_concierge",
    model=_settings.concierge_planner_model,
    description=(
        "CashTime Brand Concierge — turns a brand brief into a working creator "
        "outreach pipeline by orchestrating research, matching, enrichment, "
        "outreach drafting, scheduling, and CRM upsert via MCP."
    ),
    instruction=CONCIERGE_SYSTEM_INSTRUCTION,
    tools=ALL_TOOLS,
)
