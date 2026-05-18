from git import Repo
from services.repo_loader import load_repo

def recent_commits(repo_input):

    path = load_repo(repo_input)

    repo = Repo(path)

    output = []

    for c in repo.iter_commits(max_count=10):

        output.append(f"""
Commit : {c.hexsha[:8]}
Author : {c.author.name}
Email  : {c.author.email}
Date   : {c.committed_datetime}

Message:
{c.message.strip()}
----------------------------------------
""")

    return "\n".join(output)