from git import Repo

def recent_commits(repo_path: str):

    repo = Repo(repo_path)

    commits = []

    for commit in repo.iter_commits(max_count=10):
        commits.append({
            "message": commit.message,
            "author": str(commit.author),
        })

    return commits