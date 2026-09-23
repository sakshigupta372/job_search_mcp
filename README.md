# Job Search MCP

An MCP server that lets an AI assistant **search and retrieve job listings** through three tools.

```
AI Assistant → MCP Client → Job Search MCP → JSON sample jobs (or JSearch API) → Job results
```

No database, resume matching, or application tracker. The point of the project is:

**Build → test locally → Dockerize → deploy → connect remotely → show it working.**

## Tools

| Tool | What it does |
|---|---|
| `search_jobs(keyword, location)` | Search by role and city. Returns title, company, location, experience, job URL. |
| `get_job_details(job_id)` | Full posting: description, requirements, apply URL. |
| `filter_jobs(experience, location, job_type)` | Narrow the latest search results. |

Example:

```
search_jobs("AI Engineer", "Bangalore")
        ↓
filter_jobs(experience="0-2", job_type="Full-time")
        ↓
get_job_details("job-001")
```

By default the server searches bundled JSON in `app/data/jobs.json` so it works with no API key. Set `RAPIDAPI_KEY` to use [JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) instead.

## 1. Build and test locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -e ".[dev]"
pytest
```

Smoke-test the tools without MCP:

```bash
python -c "from app import jobs; print(jobs.search_jobs('AI Engineer', 'Bangalore'))"
```

Run the MCP server over stdio (what Cursor uses locally):

```bash
python -m app.server
```

Cursor / Claude Desktop config (`mcp.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "job-search": {
      "command": "python",
      "args": ["-m", "app.server"],
      "cwd": "C:/Users/hp/OneDrive/Documents/Desktop/Job_Search_MCP",
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

Then ask: *Find AI Engineer jobs in Bangalore.*

## 2. Dockerize

```bash
docker compose up --build
```

Health check: http://localhost:8000/health  
MCP endpoint: http://localhost:8000/mcp

## 3. Deploy

Any host that runs a Docker web service works (Render, Railway, Fly.io, a VM).

On [Render](https://render.com): New → Web Service → this repo → **Docker**. It will pick up `PORT` automatically. After deploy, `https://YOUR-SERVICE.onrender.com/health` should return `{"status":"ok"}`.

## 4. Connect remotely

Point Cursor at the deployed URL:

```json
{
  "mcpServers": {
    "job-search": {
      "url": "https://YOUR-SERVICE.onrender.com/mcp"
    }
  }
}
```

Ask the assistant to search jobs again. It should call `search_jobs` on the remote server.

## Project layout

```
app/server.py       MCP tools
app/jobs.py         search / details / filter
app/data/jobs.json  sample listings
tests/              pytest
Dockerfile          HTTP MCP on port 8000
```
