"""Multi-agent stack for CashTime Brand Concierge.

planner (root) → research_agent · matching_agent · outreach_agent (+ crm_upsert).
"""

from concierge.agents.matching import matching_agent
from concierge.agents.outreach import outreach_agent
from concierge.agents.planner import root_agent
from concierge.agents.research import research_agent

__all__ = [
    "matching_agent",
    "outreach_agent",
    "research_agent",
    "root_agent",
]
