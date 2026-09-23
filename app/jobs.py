"""Job search against bundled JSON, with an optional live JSearch API."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

DATA_PATH = Path(__file__).parent / "data" / "jobs.json"

_last_results: list[dict[str, Any]] = []


def load_sample_jobs() -> list[dict[str, Any]]:
    with DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _summary(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "experience": job.get("experience"),
        "job_type": job.get("job_type"),
        "job_url": job.get("job_url") or job.get("apply_url"),
    }


def _details(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "title": job.get("title"),
        "company": job.get("company"),
        "description": job.get("description"),
        "requirements": job.get("requirements") or [],
        "location": job.get("location"),
        "experience": job.get("experience"),
        "job_type": job.get("job_type"),
        "apply_url": job.get("apply_url") or job.get("job_url"),
    }


def _matches_keyword(job: dict[str, Any], keyword: str) -> bool:
    blob = " ".join(
        [
            str(job.get("title") or ""),
            str(job.get("company") or ""),
            str(job.get("description") or ""),
            str(job.get("job_type") or ""),
            " ".join(job.get("requirements") or []),
        ]
    ).lower()
    return keyword.lower() in blob


def _matches_location(job: dict[str, Any], location: str) -> bool:
    return location.lower() in str(job.get("location") or "").lower()


def _search_sample(keyword: str, location: str | None) -> list[dict[str, Any]]:
    jobs = load_sample_jobs()
    results = [job for job in jobs if _matches_keyword(job, keyword)]
    if location:
        results = [job for job in results if _matches_location(job, location)]
    return results


def _experience_label(raw: dict[str, Any]) -> str:
    req = raw.get("job_required_experience") or {}
    if req.get("no_experience_required"):
        return "0 years"
    months = req.get("required_experience_in_months")
    if isinstance(months, (int, float)):
        years = months / 12
        return f"{years:g} years"
    return "Not specified"


def _from_jsearch(raw: dict[str, Any]) -> dict[str, Any]:
    city = raw.get("job_city")
    country = raw.get("job_country")
    location = ", ".join(part for part in (city, country) if part) or "Not specified"
    highlights = raw.get("job_highlights") or {}
    requirements = highlights.get("Qualifications") or highlights.get("Requirements") or []
    return {
        "job_id": raw.get("job_id") or "",
        "title": raw.get("job_title"),
        "company": raw.get("employer_name"),
        "location": location,
        "experience": _experience_label(raw),
        "job_type": raw.get("job_employment_type") or "Not specified",
        "job_url": raw.get("job_apply_link"),
        "apply_url": raw.get("job_apply_link"),
        "description": raw.get("job_description"),
        "requirements": requirements,
    }


def _search_jsearch(keyword: str, location: str | None) -> list[dict[str, Any]] | None:
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return None

    query = f"{keyword} in {location}" if location else keyword
    try:
        response = httpx.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
            },
            params={"query": query, "page": 1, "num_pages": 1},
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError:
        return None

    return [_from_jsearch(item) for item in payload.get("data") or [] if item.get("job_id")]


def search_jobs(keyword: str, location: str | None = None) -> dict[str, Any]:
    """Search jobs by keyword and optional location."""
    global _last_results

    live = _search_jsearch(keyword, location)
    source = "jsearch" if live is not None else "sample"
    jobs = live if live is not None else _search_sample(keyword, location)
    _last_results = jobs
    return {
        "success": True,
        "source": source,
        "count": len(jobs),
        "jobs": [_summary(job) for job in jobs],
    }


def get_job_details(job_id: str) -> dict[str, Any]:
    """Return full details for one job id."""
    for job in _last_results:
        if job.get("job_id") == job_id:
            return {"success": True, "job": _details(job)}

    for job in load_sample_jobs():
        if job.get("job_id") == job_id:
            return {"success": True, "job": _details(job)}

    return {"success": False, "error": f"No job found for job_id={job_id}"}


def filter_jobs(
    experience: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
) -> dict[str, Any]:
    """Filter the most recent search results (or sample jobs if none yet)."""
    pool = _last_results or load_sample_jobs()
    filtered = pool

    if experience:
        needle = experience.lower()
        filtered = [job for job in filtered if needle in str(job.get("experience") or "").lower()]
    if location:
        filtered = [job for job in filtered if _matches_location(job, location)]
    if job_type:
        needle = job_type.lower()
        filtered = [job for job in filtered if needle in str(job.get("job_type") or "").lower()]

    return {
        "success": True,
        "count": len(filtered),
        "jobs": [_summary(job) for job in filtered],
    }
