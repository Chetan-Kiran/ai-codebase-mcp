Claude/Desktop
      ↓
MCP Server
 ├── Tools        ← actions
 ├── Resources    ← readable context/data
 ├── Prompts      ← reusable AI workflows
 └── Services     ← backend logic


 ```
 tools/

repo/
 ├── summarize.py
 ├── architecture.py
 ├── dependencies.py

code/
 ├── explain.py
 ├── smells.py
 ├── dead_code.py
 ├── refactor.py

git/
 ├── risks.py
 ├── contributors.py

docs/
 ├── generate_docs.py

 ```

 ```
 resources/

repo/
 ├── structure_resource.py
 ├── readme_resource.py
 ├── package_resource.py

git/
 ├── commits_resource.py
 ├── branches_resource.py

files/
 ├── file_resource.py

 ```
 ai-codebase-mcp/

├── server.py

├── tools/
│
│   ├── repo/
│   │   ├── summarize.py
│   │   ├── architecture.py
│   │   └── dependencies.py
│   │
│   ├── code/
│   │   ├── explain.py
│   │   ├── smells.py
│   │   ├── dead_code.py
│   │   └── refactor.py
│   │
│   ├── git/
│   │   ├── risks.py
│   │   └── contributors.py
│   │
│   └── docs/
│       └── generate_docs.py
│

├── resources/
│
│   ├── repo/
│   │   ├── structure_resource.py
│   │   ├── readme_resource.py
│   │   └── dependency_resource.py
│   │
│   ├── git/
│   │   ├── commits_resource.py
│   │   └── branches_resource.py
│   │
│   └── files/
│       └── file_resource.py
│

├── prompts/
│   ├── onboarding_prompt.py
│   ├── review_prompt.py
│   └── explain_prompt.py
│

├── services/
│   ├── repo_loader.py
│   ├── llm_service.py
│   ├── parser_service.py
│   ├── git_service.py
│   └── embedding_service.py

```