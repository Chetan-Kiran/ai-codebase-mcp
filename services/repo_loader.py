import os
from git import Repo

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "temp_repos"
)

os.makedirs(TEMP_DIR,exist_ok=True)

def load_repo(repo_input:str):

    if os.path.isdir(repo_input):
        return repo_input

    if repo_input.startswith("http"):

        repo_name=repo_input.split("/")[-1]
        repo_name=repo_name.replace(".git","")

        clone_path=os.path.join(
            TEMP_DIR,
            repo_name
        )

        if not os.path.exists(clone_path):

            Repo.clone_from(
                repo_input,
                clone_path
            )

        return clone_path

    raise Exception(
        "Use local folder path or GitHub URL."
    )