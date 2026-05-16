from services.parser_service import get_all_files
from services.repo_loader import load_repo

def repo_structure(repo_path: str):

    repo_path = load_repo(repo_path)
    
    files = get_all_files(repo_path)

    return "\n".join(files[:200])