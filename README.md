# AI Codebase MCP Server

An AI-powered Model Context Protocol (MCP) server built with `FastMCP` that enables AI assistants (such as Claude Desktop or Google Antigravity) to browse, index, search, analyze, and safely refactor both local repositories and remote Git projects.

This project implements robust semantic vector search using local text embedding models and isolated FAISS databases, AST structural code querying, and sandboxed safe refactoring with syntax validation.

---

## ✨ Features & Capabilities

### 🛠️ 1. Exposed MCP Tools
The server exposes **17 powerful tools** to help AI models interact with codebases:

| Category | Tool | Python Implementation | Description |
| :--- | :--- | :--- | :--- |
| **Analysis** | `summarize` | `tools/repo/summarize.py` | Generates a high-level summary of the codebase's purpose, architecture, modules, and stack via Groq (Llama 3.3). |
| | `tech_stack` | `tools/repo/tech_stack.py` | Recursively walks the repository to accurately identify language distributions and framework configurations (React, Next.js, Express, etc.). |
| | `dependency_scan` | `tools/repo/dependency_analyzer.py` | Scans project manifest files to outline package-level imports and external dependencies. |
| | `bug_scan` | `tools/code/bug_scan.py` | Performs regex-based security scans for leaks, hardcoded secrets, and standard code notes (TODOs/FIXMEs). |
| | `repo_review` | `tools/repo/repo_review.py` | Combines summary metrics and stack details into a cohesive analysis report. |
| **Navigation** | `structure` | `tools/repo/structure.py` | Lists the repository file layout (up to 500 files) excluding build caches and dependency directories. |
| | `explain_file` | `tools/code/explain_file.py` | Parses a file path locally, reads its content safely, and generates an in-depth prose description. |
| | `explain` | `tools/code/explain.py` | Explains raw code snippets in simple terms. |
| | `commits` | `tools/git/commits.py` | Pulls the last 10 git commits (author, message, date) using `GitPython`. |
| **Search** | `code_search` | `tools/ai/semantic_search.py` | Performs dense semantic vector search powered by local `sentence-transformers` + isolated FAISS index directories. |
| | `ast_query` | `tools/code/structural_search.py` | AST-powered search targeting code structures (e.g. finding implementing classes or extraction of method signatures). |
| **Action** | `safe_refactor` | `tools/code/refactor.py` | Modifies line ranges, method definitions, or full files inside a secure temporary sandbox, applying it *only* if the syntax passes validation checks. |
| | `rewrite` | `tools/code/refactor.py` | Rewrites raw code snippets based on instructions without touching local files. |
| | `cleanup_dead_code` | `tools/code/refactor.py` | Cleans up unused variables, dead imports, and redundant logging. |
| | `run_db_query` | `services/db_service.py` | Runs read/write SQL queries on the local SQLite DB tracking analysis history. |
| | `change_impact` | `tools/git/change_impact.py` | Traces staged and unstaged git diff lines, maps them to AST units, and predicts downstream breakages. |

### 📁 2. MCP Resources
Exposes raw codebase data directly to the client protocol:
*   **`repo://structure/{repo}`**: Lists the directory file map.
*   **`repo://dependencies/{repo}`**: Concatenates project configuration files (e.g., `package.json`, `requirements.txt`, `pom.xml`, `Cargo.toml`).
*   **`repo://file/{repo}/{file_path}`**: Serves raw text content of a requested workspace file.
*   **`repo://search/{repo}/{query}`**: Returns file paths containing matching string patterns.
*   **`repo://commits/{repo}`**: Retrieves git history.

### 💬 3. MCP Prompts
Exposes predefined templates to orchestrate AI execution:
*   **`onboarding`**: Standard prompt to welcome and onboard developers onto a repository.
*   **`explain_template`**: Predefined instructions for analyzing code structure.
*   **`review`**: Prompt templates for initiating security and quality code reviews.

---

## 🚀 Setup & Integration

### 📋 Prerequisites
- Python `3.10` or newer
- [uv](https://github.com/astral-sh/uv) (Recommended Python package and project manager)

### 1. Configure the Environment
Clone the repository and create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 2. Configure Claude Desktop
To integrate this server with your Claude Desktop client, add the following server configuration.

Open your Claude configuration file (located at `%APPDATA%\Claude\claude_desktop_config.json` on Windows, or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ai-codebase-mcp": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "C:\\Users\\hp\\OneDrive\\Desktop\\chetan\\ai-codebase-mcp\\main.py"
      ],
      "cwd": "C:\\Users\\hp\\OneDrive\\Desktop\\chetan\\ai-codebase-mcp"
    }
  }
}
```
> [!NOTE]
> Make sure to adjust the folder paths in `args` and `cwd` to match the exact absolute path where you cloned `ai-codebase-mcp` on your local system.

### 3. Google Antigravity & Graphify Integration
This codebase is fully compatible with **Google Antigravity**. To map codebases into semantic knowledge graphs, register the `graphifyy` tool:

```bash
# Install the Graphify package
uv add graphifyy

# Install and register the skill in Google Antigravity
uv run graphify antigravity install
```

Once installed, build the knowledge graph by running:
```bash
uv run graphify . --code-only
```
Within your coding assistant, you can then trigger `/graphify .` to parse and build the index graph of your project.

---

## 🛠️ Developer Commands

**Running in Development Mode:**
To run the server locally with a hot-reloading dev interface:
```bash
mcp dev main.py
```

**Running Tests:**
Validate project features and indexers:
```bash
uv run pytest tests/test_features.py -v
```
