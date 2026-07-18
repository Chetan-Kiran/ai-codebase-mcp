import os
import json

def analyze_dependencies(repo_path):

    package_path=os.path.join(
        repo_path,
        "package.json"
    )

    if not os.path.exists(package_path):
        return "No package.json found."

    with open(
        package_path,
        encoding="utf-8"
    ) as f:

        data=json.load(f)

    deps=data.get(
        "dependencies",
        {}
    )

    dev=data.get(
        "devDependencies",
        {}
    )

    output=[]

    output.append("Dependencies:")

    for name,version in deps.items():

        output.append(
            f"{name} : {version}"
        )

    output.append(
        "\nDev Dependencies:"
    )

    for name,version in dev.items():

        output.append(
            f"{name} : {version}"
        )

    return "\n".join(output)