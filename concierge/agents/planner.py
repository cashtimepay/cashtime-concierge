from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from concierge.agents.matching import matching_agent
from concierge.agents.outreach import outreach_agent
from concierge.agents.research import research_agent
from concierge.prompts import PLANNER_SYSTEM_INSTRUCTION
from concierge.settings import get_settings
from concierge.tools.twenty import crm_upsert

_settings = get_settings()

# Planner (root). Calls the three specialist sub-agents as tools - agent-to-agent
# collaboration - then performs the single CRM write itself via `crm_upsert`.
root_agent = Agent(
    name="cashtime_brand_concierge",
    model=_settings.concierge_planner_model,
    description=(
        "CashTime Brand Concierge planner. Turns a brand brief into a working "
        "creator-outreach pipeline by orchestrating research, matching and "
        "outreach sub-agents, then writing the campaign to the CRM."
    ),
    instruction=PLANNER_SYSTEM_INSTRUCTION,
    tools=[
        AgentTool(agent=research_agent),
        AgentTool(agent=matching_agent),
        AgentTool(agent=outreach_agent),
        crm_upsert,
    ],
)
