import os

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build"
}

def get_all_files(repo_path: str):

    files = []

    for root, dirs, filenames in os.walk(repo_path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS
        ]

        for file in filenames:

            full_path = os.path.join(root, file)

            relative_path = os.path.relpath(
                full_path,
                repo_path
            )

            files.append(relative_path)

    return sorted(files)