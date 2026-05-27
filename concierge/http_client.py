from __future__ import annotations

import httpx

from concierge.settings import get_settings


def _cf_headers() -> dict[str, str]:
    s = get_settings()
    headers: dict[str, str] = {}
    if s.cf_access_client_id and s.cf_access_client_secret:
        headers["CF-Access-Client-Id"] = s.cf_access_client_id
        headers["CF-Access-Client-Secret"] = s.cf_access_client_secret
    return headers


def internal_client(base_url: str, *, timeout: float = 30.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        headers={"User-Agent": "cashtime-concierge/0.1", **_cf_headers()},
    )


def twenty_client(*, timeout: float = 30.0) -> httpx.AsyncClient:
    s = get_settings()
    headers = {
        "User-Agent": "cashtime-concierge/0.1",
        "Authorization": f"Bearer {s.twenty_api_key}",
        "Content-Type": "application/json",
        **_cf_headers(),
    }
    return httpx.AsyncClient(base_url=s.twenty_base_url, timeout=timeout, headers=headers)
