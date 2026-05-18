 ```      
Claude/Desktop
      ↓
MCP Server
 ├── Tools        ← actions
 ├── Resources    ← readable context/data
 ├── Prompts      ← reusable AI workflows
 └── Services     ← backend logic

 ```

 ```
ai-codebase-mcp/

│
├── server.py
│
├── .env
│
├── requirements.txt
│
├── README.md
│
├── tests/
│   │
│   ├── test_structure.py
│   ├── test_summary.py
│   ├── test_explain.py
│   └── test_resources.py
│
│
├── tools/
│   │
│   ├── repo/
│   │   │
│   │   ├── summarize.py
│   │   ├── architecture.py
│   │   └── dependency_analysis.py
│   │
│   │
│   ├── code/
│   │   │
│   │   ├── explain.py
│   │   ├── smells.py
│   │   ├── dead_code.py
│   │   ├── refactor.py
│   │   └── complexity.py
│   │
│   │
│   ├── git/
│   │   │
│   │   ├── risks.py
│   │   ├── contributors.py
│   │   ├── hotspot_analysis.py
│   │   └── commit_insights.py
│   │
│   │
│   ├── ai/
│   │   │
│   │   ├── semantic_search.py
│   │   ├── embeddings.py
│   │   └── qa.py
│   │
│   │
│   └── docs/
│       │
│       ├── generate_docs.py
│       ├── generate_readme.py
│       └── api_docs.py
│
│
├── resources/
│   │
│   ├── repo/
│   │   │
│   │   ├── structure_resource.py
│   │   ├── readme_resource.py
│   │   ├── dependency_resource.py
│   │   ├── config_resource.py
│   │   └── environment_resource.py
│   │
│   │
│   ├── git/
│   │   │
│   │   ├── commits_resource.py
│   │   ├── branches_resource.py
│   │   ├── tags_resource.py
│   │   └── changelog_resource.py
│   │
│   │
│   └── files/
│       │
│       ├── file_resource.py
│       ├── folder_resource.py
│       └── search_resource.py
│
│
├── prompts/
│   │
│   ├── explain_prompt.py
│   ├── review_prompt.py
│   ├── onboarding_prompt.py
│   ├── refactor_prompt.py
│   ├── security_prompt.py
│   └── architecture_prompt.py
│
│
├── services/
|   |
│   ├── repo_loader.py
│   ├── llm_service.py
│   ├── parser_service.py
│   |── git_service.py
│   ├── embedding_service.py
│   ├── tree_sitter_service.py
│   ├── file_service.py
│   ├── dependency_service.py
│   └── cache_service.py
│
├── models/
│   │
│   ├── request_models.py
│   ├── response_models.py
│   └── schemas.py
│
│
└── temp_repos/
 ```

## RESOURCES (Claude computes)

| Feature      | MCP Type | Compute |
| :----------- | :------- | :------ |
| Structure    | Resource | Claude  |
| README       | Resource | Claude  |
| Dependencies | Resource | Claude  |
| Commits      | Resource | Claude  |
| File Reader  | Resource | Claude  |
| Search       | Resource | Claude  |

## TOOLS (Groq computes)


| Feature      | MCP Type | Compute |
| :----------- | :------- | :------ |
| Summarize    | Tool     | Groq    |
| Architecture | Tool     | Groq    |
| Explain      | Tool     | Groq    |
| Smells       | Tool     | Groq    |
| Dead_code    | Tool     | Groq    |
| Refactor     | Tool     | Groq    |
| Risks        | Tool     | Groq    |
| Docs         | Tool     | Groq    |
| Semantic_sear| Tool     | Groq    |
| Qa           | Tool     | Groq    |


## PROMPTS


| Prompt     | Purpose         |
| :--------- | :-------------- |
| onboarding | repo onboarding |
| explain    | code explain    |
| review     | security review |


```
git config user.name "Chetan_Kiran"     
git config user.email "chetankiran9666@gmail.com"
git add file path
git commit -m "B.S"
git push origin main
git log --pretty=format:"%an <%ae>"

```