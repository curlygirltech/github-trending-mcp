import os
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com/search/repositories"

mcp = FastMCP(name="github-trending")


# --- helpers -----------------------------------------------------------------

def _github_headers(raw: bool = False) -> dict:
    accept = "application/vnd.github.raw+json" if raw else "application/vnd.github+json"
    headers = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _owner_repo(repo_url: str) -> str:
    parts = repo_url.rstrip("/").split("github.com/")
    if len(parts) != 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    # Keep only the first two path segments (owner/repo), drop /tree/main etc.
    segments = parts[1].strip("/").split("/")
    if len(segments) < 2:
        raise ValueError(f"URL must include both owner and repo: {repo_url}")
    return f"{segments[0]}/{segments[1]}"


def search_repos(topic: str, days: int) -> list[dict]:
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"topic:{topic} created:>{since}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }

    response = httpx.get(GITHUB_API_URL, headers=_github_headers(), params=params, timeout=10)
    response.raise_for_status()

    items = response.json().get("items", [])
    return [
        {
            "name": repo["full_name"],
            "description": repo.get("description") or "",
            "stars": repo["stargazers_count"],
            "url": repo["html_url"],
        }
        for repo in items
    ]


# --- tools -------------------------------------------------------------------

@mcp.tool()
def get_trending_repos(topic: str, time_range: int) -> list[dict]:
    """Use this tool when the user wants to discover new or popular GitHub repositories
    for a given technology, language, or concept. Call it for prompts like "what's trending
    in Rust lately", "find new LLM projects this month", or "show me popular reinforcement
    learning repos from the past week". Returns the top 10 repos sorted by stars, each with
    name, description, star count, and URL. This is the right starting point before
    summarizing or comparing specific repos.

    Args:
        topic: A GitHub topic tag to search (e.g. 'machine-learning', 'rust', 'llm').
               Use lowercase-hyphenated form — this maps directly to GitHub topic labels.
        time_range: How many days back to look when filtering by creation date (e.g. 7 for
                    the past week, 30 for the past month). Use a shorter window for
                    "latest" queries and a longer one for broader discovery.
    """
    return search_repos(topic=topic, days=time_range)


@mcp.tool()
def summarize_repo(repo_url: str) -> str:
    """Use this tool when the user wants to understand what a specific GitHub repository
    does — its purpose, features, installation steps, or design philosophy. Call it for
    prompts like "what does this repo do", "explain this project to me", "is this library
    a good fit for my use case", or "give me a summary of X". Fetches the raw README
    markdown and returns it as text so you can synthesize an answer in your own words.
    Do NOT call this for every repo returned by get_trending_repos — only fetch READMEs
    for repos the user has explicitly asked about or that are directly relevant to their
    follow-up question.

    Args:
        repo_url: Full GitHub URL of the repo (e.g. 'https://github.com/owner/repo').
                  Must be a github.com URL pointing to the repo root, not a file or PR link.
    """
    owner_repo = _owner_repo(repo_url)
    response = httpx.get(
        f"https://api.github.com/repos/{owner_repo}/readme",
        headers=_github_headers(raw=True),
        timeout=10,
    )
    if response.status_code == 404:
        return "No README found for this repository."
    response.raise_for_status()
    return response.text


@mcp.tool()
def compare_repos(repo_urls: list[str]) -> list[dict]:
    """Use this tool when the user wants to evaluate or choose between multiple specific
    GitHub repositories. Call it for prompts like "which of these projects is more active",
    "compare A vs B", "which repo has better community support", or "help me pick between
    these options". Returns structured metadata for each repo — stars, forks, open issues,
    language, license, topics, and timestamps — so you can reason across them in a single
    response. Prefer this over calling summarize_repo multiple times when the user's goal
    is comparison rather than deep understanding of any one project. Requires at least two
    URLs; there is no hard maximum but keep it reasonable (under 10) to avoid rate limiting.

    Args:
        repo_urls: List of full GitHub repo URLs to compare
                   (e.g. ['https://github.com/owner/repo1', 'https://github.com/owner/repo2']).
                   Each must be a valid github.com repo root URL.
    """
    results = []
    for url in repo_urls:
        owner_repo = _owner_repo(url)
        response = httpx.get(
            f"https://api.github.com/repos/{owner_repo}",
            headers=_github_headers(),
            timeout=10,
        )
        response.raise_for_status()
        r = response.json()
        results.append({
            "name": r["full_name"],
            "description": r.get("description") or "",
            "url": r["html_url"],
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "open_issues": r["open_issues_count"],
            "watchers": r["watchers_count"],
            "language": r.get("language") or "",
            "license": (r.get("license") or {}).get("spdx_id") or "",
            "topics": r.get("topics", []),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "default_branch": r["default_branch"],
        })
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
