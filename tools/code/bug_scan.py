import os

PATTERNS=[
    "TODO",
    "FIXME",
    "password=",
    "api_key",
    "SECRET"
]

def scan_bugs(repo_path):

    findings=[]

    for root,dirs,files in os.walk(repo_path):

        for file in files:

            path=os.path.join(
                root,
                file
            )

            try:

                with open(
                    path,
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    text=f.read()

                for p in PATTERNS:

                    if p.lower() in text.lower():

                        findings.append(
                            f"{file} -> {p}"
                        )

            except:
                pass

    if not findings:
        return "No issues found."

    return "\n".join(findings)