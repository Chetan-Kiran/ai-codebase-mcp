import os

def detect_stack(repo_path):

    found=[]

    files=os.listdir(repo_path)

    if "package.json" in files:
        found.append("Node.js / JavaScript")

        package=open(
            os.path.join(repo_path,"package.json"),
            encoding="utf-8",
            errors="ignore"
        ).read().lower()

        if "react" in package:
            found.append("React")

        if "express" in package:
            found.append("Express")

        if "next" in package:
            found.append("Next.js")

    if "requirements.txt" in files:
        found.append("Python")

    if "pom.xml" in files:
        found.append("Java Maven")

    if "build.gradle" in files:
        found.append("Gradle")

    if "dockerfile" in [f.lower() for f in files]:
        found.append("Docker")

    if not found:
        return "Unknown stack"

    return "\n".join(found)