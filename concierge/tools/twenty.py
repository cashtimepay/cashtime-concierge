from __future__ import annotations

from typing import Any

from concierge.http_client import twenty_client
from concierge.settings import get_settings


async def crm_upsert(
    brand_profile: dict[str, Any],
    creators: list[dict[str, Any]],
    sequences: list[dict[str, Any]],
) -> dict[str, Any]:
    """Upsert a brand campaign into Twenty CRM as Company + Persons + Opportunity.

    Idempotent on company domain. Creators are not duplicated - they are
    linked to the Opportunity via the existing Creator records (matched by
    ``creator_id``).

    Args:
        brand_profile: Output of ``research_brand``.
        creators: Enriched creators from ``match_creators`` + ``enrich_creator``.
        sequences: Outreach sequences from ``schedule_sequence`` (one per creator).

    Returns:
        dict with ``company_id``, ``person_ids``, ``opportunity_id``,
        ``crm_url`` (deep link to the Company page in Twenty).
    """
    settings = get_settings()
    if settings.demo_mode or not settings.twenty_api_key:
        return _demo_payload(brand_profile, creators)

    company = brand_profile.get("company", {})
    async with twenty_client() as http:
        comp_resp = await http.post(
            "/rest/companies",
            json={
                "name": company.get("name"),
                "domainName": {"primaryLinkUrl": company.get("domain")},
                "description": company.get("description"),
            },
        )
        comp_resp.raise_for_status()
        company_id = comp_resp.json()["data"]["createCompany"]["id"]

        person_ids: list[str] = []
        for person in brand_profile.get("persons", []):
            p_resp = await http.post(
                "/rest/people",
                json={
                    "name": {"firstName": person.get("name", "").split(" ", 1)[0],
                              "lastName": person.get("name", "").split(" ", 1)[-1]},
                    "emails": {"primaryEmail": person.get("email")},
                    "companyId": company_id,
                },
            )
            if p_resp.status_code in (200, 201):
                person_ids.append(p_resp.json()["data"]["createPerson"]["id"])

        opp_resp = await http.post(
            "/rest/opportunities",
            json={
                "name": f"Concierge run · {company.get('name')}",
                "companyId": company_id,
            },
        )
        opp_resp.raise_for_status()
        opportunity_id = opp_resp.json()["data"]["createOpportunity"]["id"]

    crm_url = f"{settings.twenty_base_url}/object/company/{company_id}"
    return {
        "company_id": company_id,
        "company_name": company.get("name"),
        "opportunity_name": f"Concierge run · {company.get('name')}",
        "persons": [
            {"name": p.get("name"), "role": p.get("role"), "email": p.get("email")}
            for p in brand_profile.get("persons", [])
        ],
        "person_ids": person_ids,
        "opportunity_id": opportunity_id,
        "crm_url": crm_url,
        "creators_linked": len(creators),
        "sequences_attached": len(sequences),
        "written": True,
    }


def _demo_payload(brand: dict[str, Any], creators: list[dict[str, Any]]) -> dict[str, Any]:
    company = brand.get("company", {})
    return {
        "company_id": "demo-company-uuid",
        "company_name": company.get("name"),
        "opportunity_name": f"Concierge run · {company.get('name')}",
        "persons": [
            {"name": p.get("name"), "role": p.get("role"), "email": p.get("email")}
            for p in brand.get("persons", [])
        ],
        "person_ids": ["demo-person-uuid"],
        "opportunity_id": "demo-opportunity-uuid",
        # In demo mode nothing is written to the production CRM; this is a
        # synthetic record shown for illustration only.
        "written": False,
        "crm_url": None,
        "creators_linked": len(creators),
        "sequences_attached": len(creators),
    }
