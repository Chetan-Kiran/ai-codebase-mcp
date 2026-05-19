from urllib.parse import unquote

def normalize_repo(repo):
    
    repo = unquote(repo)

    repo = repo.strip('"')
    repo = repo.strip("'")

    return repo