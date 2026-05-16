import os
from services.repo_loader import load_repo

def get_all_files(repo_path):
    
    repo_path = load_repo(repo_path)
    result = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in [".git", "venv", ".venv", "__pycache__"]]

        for file in files:
            result.append(os.path.join(root, file))

    return result