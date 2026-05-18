import os

from services.repo_loader import load_repo
from services.parser_service import get_all_files

def search_resource(repo,query):

    path = load_repo(repo)

    files = get_all_files(path)

    matches=[]

    for f in files:

        full=os.path.join(path,f)

        try:

            with open(
                full,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                content=file.read()

                if query.lower() in content.lower():

                    matches.append(f)

        except:
            pass

    return "\n".join(matches[:100])