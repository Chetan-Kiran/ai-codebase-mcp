from services.repo_loader import load_repo
from services.parser_service import get_all_files
from services.llm_service import ask_llm

def repo_summary(repo_input:str):

    path = load_repo(repo_input)

    files = get_all_files(path)

    prompt = f"""
Analyze this repository.

FILES:

{chr(10).join(files[:300])}

Explain:

1. Project purpose
2. Architecture
3. Tech stack
4. Important modules
5. Folder organization
"""

    return ask_llm(prompt)