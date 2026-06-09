"""Backward-compatible entry point.

The multi-agent stack lives in ``concierge.agents``. This module re-exports the
root planner so existing imports (``from concierge.agent import root_agent``)
keep working. ADK's `adk web` / `adk run` also discover `root_agent` here.
"""

from __future__ import annotations

from concierge.agents import root_agent

__all__ = ["root_agent"]
