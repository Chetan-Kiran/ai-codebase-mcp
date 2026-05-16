from services.parser_service import get_all_files
from services.llm_service import ask_llm
from services.repo_loader import load_repo

def repo_summary(repo_path: str):
    
    repo_path = load_repo(repo_path)
    files = get_all_files(repo_path)

    prompt = f"""
    Analyze this repository.

    Files:
    {files[:100]}

    Explain:
    - project purpose
    - architecture
    - technologies
    - important modules
    """

    return ask_llm(prompt)