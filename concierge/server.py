from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from concierge.agent import root_agent
from concierge.observability import setup_observability
from concierge.pipeline import stream_pipeline
from concierge.settings import get_settings

setup_observability()
log = structlog.get_logger()

app = FastAPI(
    title="CashTime Brand Concierge",
    description=(
        "Customer-facing AI agent that turns a brand brief into a working creator "
        "outreach pipeline. Submission for Google for Startups AI Agents Challenge 2026."
    ),
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()


_session_service = InMemorySessionService()
_runner = Runner(
    app_name="cashtime_brand_concierge",
    agent=root_agent,
    session_service=_session_service,
)


class BriefRequest(BaseModel):
    brand_url: str = Field(..., examples=["https://chapterhouse.demo"])
    goal: str = Field(..., examples=["100 trial signups per month from indie-fiction readers"])
    budget_monthly_usd: float = Field(..., examples=[5000])
    session_id: str | None = None


@app.get("/health")
@app.get("/healthz")  # kept for parity; note: Google Frontend reserves /healthz at the edge
async def health() -> dict[str, str]:
    return {"status": "ok", "demo_mode": str(get_settings().demo_mode)}


@app.get("/version")
async def version() -> dict[str, str]:
    return {"service": "cashtime-concierge", "version": "0.1.0"}


@app.post("/concierge/run")
async def run_concierge(brief: BriefRequest) -> EventSourceResponse:
    session_id = brief.session_id or f"sess-{uuid.uuid4().hex[:12]}"
    log.info("concierge.run.start", session_id=session_id, brand_url=brief.brand_url)

    user_message = (
        f"Brand URL: {brief.brand_url}\n"
        f"Goal: {brief.goal}\n"
        f"Monthly budget (USD): {brief.budget_monthly_usd}\n\n"
        "Run the full pipeline."
    )

    async def event_stream() -> AsyncGenerator[dict, None]:
        try:
            if get_settings().demo_mode:
                # Deterministic offline replay — same event shape, no LLM.
                async for payload in stream_pipeline(
                    brief.brand_url, brief.goal, brief.budget_monthly_usd
                ):
                    yield {"event": payload["type"], "data": json.dumps(payload)}
                    await asyncio.sleep(0)
            else:
                # Live model-driven multi-agent run via ADK.
                await _session_service.create_session(
                    app_name="cashtime_brand_concierge",
                    user_id="brand-ui",
                    session_id=session_id,
                )
                content = types.Content(role="user", parts=[types.Part(text=user_message)])
                async for event in _runner.run_async(
                    user_id="brand-ui",
                    session_id=session_id,
                    new_message=content,
                ):
                    payload = _serialise_event(event)
                    if payload is None:
                        continue
                    yield {"event": payload["type"], "data": json.dumps(payload)}
                    await asyncio.sleep(0)
        except Exception as exc:
            log.exception("concierge.run.error", session_id=session_id)
            yield {"event": "error", "data": json.dumps({"error": str(exc)})}
        finally:
            log.info("concierge.run.done", session_id=session_id)
            yield {"event": "done", "data": json.dumps({"session_id": session_id})}

    return EventSourceResponse(event_stream())


def _serialise_event(event) -> dict | None:
    parts_text: list[str] = []
    tool_calls: list[dict] = []
    tool_results: list[dict] = []

    content = getattr(event, "content", None)
    if content is not None:
        for part in content.parts or []:
            if getattr(part, "text", None):
                parts_text.append(part.text)
            fcall = getattr(part, "function_call", None)
            if fcall is not None:
                tool_calls.append({"name": fcall.name, "args": dict(fcall.args or {})})
            fresp = getattr(part, "function_response", None)
            if fresp is not None:
                tool_results.append({"name": fresp.name, "response": dict(fresp.response or {})})

    if not (parts_text or tool_calls or tool_results):
        return None

    kind = "text"
    if tool_calls:
        kind = "tool_call"
    elif tool_results:
        kind = "tool_result"

    return {
        "type": kind,
        "text": "".join(parts_text) if parts_text else None,
        "tool_calls": tool_calls or None,
        "tool_results": tool_results or None,
    }


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "concierge.server:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
