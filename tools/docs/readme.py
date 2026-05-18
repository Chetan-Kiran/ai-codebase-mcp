from services.parser_service import get_all_files
from services.llm_service import ask_llm

def generate_readme(repo_path):

    files=get_all_files(repo_path)

    prompt=f"""

Generate README.

Files:

{files[:100]}

"""

    return ask_llm(prompt)