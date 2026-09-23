from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from app import jobs

load_dotenv()

TEMPLATES_DIR = Path(__file__).parent / "templates"

mcp = MCPServer(
    name="job-search",
    instructions=(
        "Search and retrieve job listings. Use search_jobs for keyword + location, "
        "filter_jobs to narrow those results, and get_job_details for a full posting."
    ),
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "job-search"})


@mcp.custom_route("/", methods=["GET"])
async def index(_request: Request) -> HTMLResponse:
    html = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@mcp.custom_route("/api/search", methods=["POST"])
async def api_search(request: Request) -> Response:
    try:
        body = await request.json()
    except ValueError:
        return JSONResponse({"success": False, "error": "Invalid JSON body."}, status_code=400)

    keyword = (body.get("keyword") or "").strip()
    if not keyword:
        return JSONResponse({"success": False, "error": "keyword is required."}, status_code=400)

    location = (body.get("location") or "").strip() or None
    result = jobs.search_jobs(keyword=keyword, location=location)
    return JSONResponse(result)


@mcp.custom_route("/api/filter", methods=["POST"])
async def api_filter(request: Request) -> Response:
    try:
        body = await request.json()
    except ValueError:
        return JSONResponse({"success": False, "error": "Invalid JSON body."}, status_code=400)

    result = jobs.filter_jobs(
        experience=(body.get("experience") or "").strip() or None,
        location=(body.get("location") or "").strip() or None,
        job_type=(body.get("job_type") or "").strip() or None,
    )
    return JSONResponse(result)


@mcp.custom_route("/api/jobs/{job_id}", methods=["GET"])
async def api_job_details(request: Request) -> JSONResponse:
    job_id = request.path_params["job_id"]
    result = jobs.get_job_details(job_id)
    return JSONResponse(result, status_code=200 if result.get("success") else 404)


@mcp.tool()
def search_jobs(keyword: str, location: str = "") -> dict:
    """Search jobs by keyword and location.

    Example: search_jobs("AI Engineer", "Bangalore")
    Returns title, company, location, experience, and job URL.
    """
    return jobs.search_jobs(keyword=keyword, location=location or None)


@mcp.tool()
def get_job_details(job_id: str) -> dict:
    """Get details for a specific job: title, company, description, requirements, location, apply URL."""
    return jobs.get_job_details(job_id)


@mcp.tool()
def filter_jobs(experience: str = "", location: str = "", job_type: str = "") -> dict:
    """Filter the latest search results by experience, location, or job type.

    Run search_jobs first. Example: filter_jobs(experience="0-2", location="Bangalore", job_type="Full-time")
    """
    return jobs.filter_jobs(
        experience=experience or None,
        location=location or None,
        job_type=job_type or None,
    )


def main() -> None:
    transport = os.getenv("TRANSPORT", "stdio").strip().lower()
    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    if transport in {"http", "streamable-http", "sse"}:
        chosen = "sse" if transport == "sse" else "streamable-http"
        mcp.run(transport=chosen, host=host, port=port)
        return

    raise SystemExit(f"Unknown TRANSPORT={transport!r}. Use stdio, streamable-http, or sse.")


if __name__ == "__main__":
    main()
