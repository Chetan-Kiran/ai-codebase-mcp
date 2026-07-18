import os

from tools.code.explain import explain_code

def explain_file(
    repo_path,
    file_path
):

    path=os.path.join(
        repo_path,
        file_path
    )

    if not os.path.exists(path):

        return "File not found."

    with open(
        path,
        encoding="utf-8",
        errors="ignore"
    ) as f:

        code=f.read()

    return explain_code(code)