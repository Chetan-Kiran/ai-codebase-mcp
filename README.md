# AI Codebase MCP Server

This is an MCP (Model Context Protocol) Server built on `FastMCP` that enables AI clients (like Claude Desktop) to interact with, search, and analyze repositories (both local folders and cloned GitHub repositories).

---

## 🚀 Current Project Status & Features

### 🛠️ 1. Ready & Functional Tools
The following tools are registered in [main.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/main.py) and have active implementations:

| Tool Name | Python Path | Description / Notes |
| :--- | :--- | :--- |
| `summarize` | [summarize.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/repo/summarize.py) | Analyzes file paths and asks Llama 3.3 (via Groq) to provide project purpose, architecture, stack, modules, etc. |
| `tech_stack` | [tech_stack.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/repo/tech_stack.py) | Scans key config files (`package.json`, `requirements.txt`, etc.) to detect Node, Python, Java, Docker stack. |
| `dependency_scan` | [dependency_analyzer.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/repo/dependency_analyzer.py) | Parses `package.json` to extract `dependencies` and `devDependencies`. *(Note: Only supports JS/TS projects right now).* |
| `bug_scan` | [bug_scan.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/code/bug_scan.py) | Performs simple pattern scan for comments/secrets (`TODO`, `FIXME`, `password=`, `api_key`, `SECRET`). |
| `repo_review` | [repo_review.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/repo/repo_review.py) | Combines stack detection and LLM summary to output a repo-wide review with suggestions. |
| `code_search` | [semantic_search.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/ai/semantic_search.py) | Case-insensitive text query matching across repository files. *(Note: Implemented as keyword search, not vector embeddings).* |
| `structure` | [structure.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/repo/structure.py) | Walk the directory (ignoring build artifacts/caches) and lists up to 500 file paths. |
| `explain` | [explain.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/code/explain.py) | Sends a raw code snippet to Groq LLM and asks for a simple explanation. |
| `commits` | [commits.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/git/commits.py) | Uses `GitPython` to iterate and format the last 10 git commits (hash, author, date, message). |
| `readme` | [readme.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/docs/readme.py) | Prompts Groq LLM to automatically generate a repository README based on a list of file paths. |
| `rewrite` | [refactor.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/code/refactor.py) | Prompts LLM to rewrite or refactor a code snippet according to user instructions. |
| `cleanup_dead_code` | [refactor.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/code/refactor.py) | Specialization of `rewrite` instructing LLM to strip dead code, unused variables, and unreachable code. |
| `run_db_query` | [db_service.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/services/db_service.py) | Executes SELECT queries (returning output) or modifications on local SQLite Database `project_data.db` (which tracks analysis history). |

### 📁 2. Ready & Functional Resources
MCP resources are registered to provide read-only context to the model:

*   **`repo://structure/{repo}`**: Lists repository layout/files using [structure_resource.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/resources/repo/structure_resource.py).
*   **`repo://dependencies/{repo}`**: Reads and concatenates contents of `requirements.txt`, `package.json`, `pom.xml`, and `Cargo.toml` if found in the repository using [dependency_resource.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/resources/repo/dependency_resource.py).
*   **`repo://file/{repo}/{file_path}`**: Loads raw contents of a specific file inside the repo using [file_resource.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/resources/files/file_resource.py).
*   **`repo://search/{repo}/{query}`**: Returns a list of filenames containing the matching query using [search_resource.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/resources/files/search_resource.py).
*   **`repo://commits/{repo}`**: Fetches the recent 10 commits via [commits_resource.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/resources/git/commits_resource.py).

### 💬 3. Ready & Functional Prompts
Prompt templates help LLM models structure queries:

*   **`onboarding`**: Prompts the model to onboarding standard repo details ([onboarding_prompt.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/prompts/onboarding_prompt.py)).
*   **`explain_template`**: Predefined prompt to request code explanation ([explain_prompt.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/prompts/explain_prompt.py)).
*   **`review`**: Predefined prompt to request code quality and security review ([review_prompt.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/prompts/review_prompt.py)).

---

## ⚠️ Known Bugs & Limitations

> [!WARNING]
> ### 1. Shadowing / Recursion Bug in `explain_file` Tool
> In [main.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/main.py#L36-L47):
> ```python
> from tools.code.explain_file import explain_file
> ...
> @mcp.tool()
> def explain_file(repo:str, file_path:str):
>     path = load_repo(repo)
>     return explain_file(path, file_path) # Recursion Error / Infinite Self-Call
> ```
> The registered tool shadows the import, causing it to call itself infinitely (raising `RecursionError`). To fix this, import the tool function as an alias (e.g., `import explain_file as explain_file_tool`).

> [!IMPORTANT]
> ### 2. Semantic Search is Actually Keyword Search
> The tools `code_search` / `semantic_search` do not perform vector embeddings or similarity searches. They walk directories and do a simple string `query.lower() in line.lower()`. The [embedding_service.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/services/embedding_service.py) and [embeddings.py](file:///c:/Users/hp/OneDrive/Desktop/chetan/ai-codebase-mcp/tools/ai/embeddings.py) files are currently empty.

> [!NOTE]
> ### 3. Limited Dependency Parsing in Tools
> While the **Resource** `repo://dependencies/{repo}` checks Python/JS/Java/Rust configurations, the **Tool** `dependency_scan` only searches and parses `package.json`. If it's a Python project, it fails to find dependencies despite detecting Python.

---

## 🛠️ Development & Execution Setup

1.  **Environment Variables**:
    Create or verify `.env` in the root:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    ```

2.  **Activate Virtual Environment**:
    ```powershell
    .venv\Scripts\activate.bat
    ```

3.  **Run Development Server**:
    Ensure the dependencies are installed (`uv sync` or `pip install -r requirements.txt`). Then run with the MCP dev CLI:
    ```bash
    mcp dev main.py
    ```

# Current project holds

* ast_query – query the codebase's AST
* bug_scan – scan for bugs
* change_impact – assess impact of a change
* cleanup_dead_code – find/remove dead code
* code_search – search code
* commits – look at commit history
* dependency_scan – scan dependencies
* explain / explain_file – explain code or a specific file
* readme – generate/view README
* repo_review – review a repo
* rewrite – rewrite code
* run_db_query – run a database query
* safe_refactor – refactor safely
* structure – show repo structure
* summarize – summarize code
* tech_stack – identify tech stack



git commit --date="2024-01-15 14:30:00" -m "Adding old work"

