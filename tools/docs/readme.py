from services.llm_service import ask_llm
from services.parser_service import get_all_files

def generate_readme(repo_path: str):

    files = get_all_files(repo_path)

    prompt = f"""
    Generate professional README for this repository.

    Files:
    {files[:100]}
    """

    return ask_llm(prompt)