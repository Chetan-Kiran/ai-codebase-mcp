from tools.repo.summarize import repo_summary
from tools.repo.tech_stack import detect_stack

def review_repo(repo_path):

    summary=repo_summary(repo_path)

    stack=detect_stack(repo_path)

    return f"""
Repository Review

TECH STACK
----------
{stack}

SUMMARY
-------
{summary}

SUGGESTIONS
-----------
- Add tests
- Improve documentation
- Check dependency versions
"""