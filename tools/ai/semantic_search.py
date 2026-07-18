import os

def semantic_search(repo_path,query):

    results=[]

    query=query.lower()

    for root,dirs,files in os.walk(repo_path):

        for file in files:

            path=os.path.join(root,file)

            try:

                with open(
                    path,
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    lines=f.readlines()

                for i,line in enumerate(lines):

                    if query in line.lower():

                        results.append(
                            f"{file}:{i+1} -> {line.strip()}"
                        )

            except:
                pass

    if not results:
        return "No matches found."

    return "\n".join(results[:50])