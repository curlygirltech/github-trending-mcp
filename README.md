# github-trend-mcp

A Model Context Protocol (MCP) server that gives Claude live visibility into what the open source community is actively building. Search GitHub for emerging repositories by topic, summarize project READMEs, and compare multiple repos to surface ecosystem patterns -- all through natural language.

---

## Why This Exists

GitHub's official trending page is a black box. This MCP uses the GitHub Search API to build a more transparent and configurable version of "trending" -- recently created repositories ranked by star velocity within a topic area. The result is a research workflow where you can ask Claude questions like:

- "What are the most-starred AI agent repos created in the last two weeks?"
- "Summarize what this repo actually does"
- "Compare these three projects and tell me what problems they're each trying to solve"

---

## Tech Stack

- **Python** -- core language
- **MCP Python SDK** -- exposes tools to Claude via the Model Context Protocol
- **httpx** -- async HTTP client for GitHub API requests
- **GitHub Search API** -- the data source (official, authenticated, reliable)
- **python-dotenv** -- environment variable management for your GitHub token

---

## Tools

### `get_trending_repos`
Searches GitHub for recently created repositories in a given topic area, sorted by star count. Accepts a topic string and a time range in days so you can define what "trending" means for your use case.

```
topic: "ai-agents"
time_range_days: 14
```

### `summarize_repo`
Fetches the raw README for any GitHub repository by URL. Claude reads and summarizes it directly -- no secondary model call needed.

```
repo_url: "https://github.com/owner/repo"
```

### `compare_repos`
Accepts a list of repository URLs and returns structured metadata for each -- name, description, star count, language, and topics. Gives Claude what it needs to reason across multiple projects and surface common themes or differences.

```
repo_urls: ["https://github.com/owner/repo-a", "https://github.com/owner/repo-b"]
```

---

## Project Structure

```
github-trend-mcp/
├── server.py          # MCP server and tool definitions
├── github.py          # GitHub API client functions
├── requirements.txt   # Dependencies
├── .env.example       # Environment variable template
└── README.md
```

---

## Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/your-username/github-trend-mcp.git
cd github-trend-mcp
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up your GitHub token**

Copy `.env.example` to `.env` and add your token. A free GitHub account gives you 5,000 API requests per hour -- more than enough.

```bash
cp .env.example .env
```

```
GITHUB_TOKEN=your_token_here
```

**4. Connect to Claude**

Add this server to your Claude Desktop or Claude Code MCP config:

```json
{
  "mcpServers": {
    "github-trend-mcp": {
      "command": "python",
      "args": ["path/to/github-trend-mcp/server.py"]
    }
  }
}
```

---

## Example Prompts

Once connected, try these in Claude:

- *"Find the most-starred repositories about multi-agent systems created in the last 30 days"*
- *"Summarize the README for [repo URL] in plain English"*
- *"Compare these three repos and tell me which problem each one is trying to solve"*
- *"What languages are most common in trending AI tooling repos right now?"*

---

## A Note on "Trending"

GitHub's official trending page uses an undocumented algorithm. This MCP uses a transparent proxy: repositories created within your specified time window, ranked by total stars. This gives you a configurable, reproducible definition of trending that you can adjust based on your research needs.

---

## License

MIT
