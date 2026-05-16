import os
import tempfile
from git import Repo

def load_repo(repo_input: str):
    """
    Accepts:
    - local folder path
    - github repo url

    Returns:
    local usable path
    """

    # LOCAL PATH
    if os.path.exists(repo_input):
        return repo_input

    # GITHUB URL
    if repo_input.startswith("https://github.com"):
        temp_dir = tempfile.mkdtemp()

        Repo.clone_from(repo_input, temp_dir)

        return temp_dir

    raise Exception("Invalid repository input")