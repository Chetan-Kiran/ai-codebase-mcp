from services.repo_loader import load_repo
from services.parser_service import get_all_files

def structure_resource(repo):

    path = load_repo(repo)

    files = get_all_files(path)

    return "\n".join(files[:500])