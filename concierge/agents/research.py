from __future__ import annotations

from google.adk.agents import Agent

from concierge.grounding import ground_taxonomy
from concierge.prompts import RESEARCH_AGENT_INSTRUCTION
from concierge.settings import get_settings
from concierge.tools.aibmr import research_brand

_settings = get_settings()

research_agent = Agent(
    name="research_agent",
    model=_settings.concierge_worker_model,
    description=(
        "Researches a brand from its URL, goal and budget, then grounds the "
        "profile against CashTime's canonical taxonomy via Vertex AI Search so "
        "the brand maps to real niche enums (no hallucinated niches)."
    ),
    instruction=RESEARCH_AGENT_INSTRUCTION,
    tools=[research_brand, ground_taxonomy],
)
