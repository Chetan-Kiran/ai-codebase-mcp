from mcp.server.fastmcp import FastMCP

from services.repo_loader import load_repo
from services.normalize_repo import normalize_repo
from services.db_service import execute_db, query_db

from tools.repo.structure import repo_structure
from tools.repo.summarize import repo_summary
from tools.code.explain import explain_code
from tools.git.commits import recent_commits
from tools.docs.readme import generate_readme
from tools.repo.tech_stack import detect_stack
from tools.repo.dependency_analyzer import analyze_dependencies
from tools.code.bug_scan import scan_bugs
from tools.repo.repo_review import review_repo
from tools.ai.semantic_search import semantic_search
from tools.code.explain_file import explain_file
from tools.code.refactor import rewrite_code, remove_dead_code

from resources.repo.structure_resource import structure_resource
from resources.repo.dependency_resource import dependency_resource
from resources.files.file_resource import file_resource
from resources.files.search_resource import search_resource
from resources.git.commits_resource import commits_resource

from prompts.onboarding_prompt import onboarding_prompt
from prompts.explain_prompt import explain_prompt
from prompts.review_prompt import review_prompt

mcp=FastMCP("AI-Codebase-MCP")

####################
# TOOLS
####################

@mcp.tool()
def explain_file(
    repo:str,
    file_path:str
):

    path=load_repo(repo)

    return explain_file(
        path,
        file_path
    )

@mcp.tool()
def code_search(
    repo:str,
    query:str
):

    """
    Search across repository code.
    """

    path=load_repo(repo)

    return semantic_search(
        path,
        query
    )

@mcp.tool()
def repo_review(repo:str):

    """
    AI repository review.
    """

    path=load_repo(repo)

    return review_repo(path)

@mcp.tool()
def bug_scan(repo:str):

    """
    Scan repository for common issues.
    """

    path=load_repo(repo)

    return scan_bugs(path)

@mcp.tool()
def dependency_scan(repo:str):

    """
    Analyze dependencies.

    Input:
    - local folder path
    - GitHub URL
    """

    path=load_repo(repo)

    return analyze_dependencies(path)

@mcp.tool()
def tech_stack(repo:str):

    """
    Detect project tech stack.

    Input:
    - local folder path
    - GitHub URL
    """

    path=load_repo(repo)

    return detect_stack(path)



@mcp.tool()
def structure(repo:str):

    """
    Get repository structure.

    Input:
    - local folder path
    - GitHub URL
    """

    path=load_repo(repo)

    return repo_structure(path)



@mcp.tool()
def summarize(repo:str):

    """
    Summarize repository.

    Input:
    - local folder path
    - GitHub URL
    """

    path=load_repo(repo)

    return repo_summary(path)



@mcp.tool()
def explain(code:str):

    """
    Explain code snippet.
    """

    return explain_code(code)



@mcp.tool()
def commits(repo:str):

    """
    Recent git commits.

    Input:
    - local folder path
    - GitHub URL
    """

    path=load_repo(repo)

    return recent_commits(path)

@mcp.tool()
def readme(repo:str):

    """
    Generate README.

    Input:
    - local folder path
    - GitHub URL
    """

    path=load_repo(repo)

    return generate_readme(path)


@mcp.tool()
def rewrite(code: str, instructions: str = "Refactor this code."):
    """
    Rewrite or refactor a code snippet based on instructions.
    """
    return rewrite_code(code, instructions)

@mcp.tool()
def cleanup_dead_code(code: str):
    """
    Remove dead code from a snippet.
    """
    return remove_dead_code(code)

@mcp.tool()
def run_db_query(query: str):
    """
    Execute a query on the project database and return results.
    """
    try:
        if query.strip().lower().startswith("select"):
            return str(query_db(query))
        else:
            return execute_db(query)
    except Exception as e:
        return f"Database error: {str(e)}"


@mcp.resource("repo://structure/{repo}")
def structure_resource_mcp(repo:str):

    repo = normalize_repo(repo)
    path = load_repo(repo)
    print("final path:", path)
    return structure_resource(path)

@mcp.resource(
    "repo://dependencies/{repo}"
)
def dependencies_resource_mcp(repo:str):

    repo = normalize_repo(repo)
    path = load_repo(repo)

    return dependency_resource(path)

@mcp.resource(
    "repo://file/{repo}/{file_path}"
)
def file_resource_mcp(repo:str,file_path:str):

    repo = normalize_repo(repo)
    file_path = normalize_repo(file_path)

    path = load_repo(repo)

    return file_resource(
        path,
        file_path
    )

@mcp.resource(
    "repo://search/{repo}/{query}"
)
def search_resource_mcp(repo:str,query:str):

    repo = normalize_repo(repo)
    query = normalize_repo(query)

    path = load_repo(repo)

    return search_resource(
        path,
        query
    )

@mcp.resource(
    "repo://commits/{repo}"
)
def commits_resource_mcp(repo:str):

    repo = normalize_repo(repo)
    path = load_repo(repo)

    return commits_resource(path)



@mcp.prompt()
def onboarding():

    return onboarding_prompt()

@mcp.prompt()
def explain_template():

    return explain_prompt("{code}")

@mcp.prompt()
def review():

    return review_prompt("{code}")


if __name__=="__main__":
    mcp.run()