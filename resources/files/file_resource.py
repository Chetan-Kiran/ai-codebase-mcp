import os
from services.repo_loader import load_repo

def file_resource(repo,file_path):

    path = load_repo(repo)

    full = os.path.join(path,file_path)

    if not os.path.exists(full):

        return "File not found"

    with open(
        full,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        return f.read()