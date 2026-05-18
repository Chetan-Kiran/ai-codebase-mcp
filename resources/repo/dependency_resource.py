import os
from services.repo_loader import load_repo

FILES = [
    "requirements.txt",
    "package.json",
    "pom.xml",
    "Cargo.toml"
]

def dependency_resource(repo):

    path = load_repo(repo)

    result = []

    for file in FILES:

        fp = os.path.join(path,file)

        if os.path.exists(fp):

            with open(fp,"r",encoding="utf-8",errors="ignore") as f:

                result.append(
                    f"\n===== {file} =====\n"
                )

                result.append(f.read())

    return "\n".join(result)