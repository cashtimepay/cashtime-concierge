from __future__ import annotations

import logging

import structlog
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from concierge.settings import get_settings


def setup_observability() -> None:
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
    )

    resource = Resource.create({
        "service.name": "cashtime-concierge",
        "service.version": "0.1.0",
        "cloud.provider": "gcp",
        "cloud.account.id": settings.google_cloud_project,
        "cloud.region": settings.google_cloud_location,
    })
    provider = TracerProvider(resource=resource)
    if settings.google_cloud_project and not settings.demo_mode:
        try:
            exporter = CloudTraceSpanExporter(project_id=settings.google_cloud_project)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception:
            logging.getLogger(__name__).warning("Cloud Trace exporter init failed; tracing local only")
    trace.set_tracer_provider(provider)
