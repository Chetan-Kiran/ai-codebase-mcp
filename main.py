from mcp.server.fastmcp import FastMCP

from tools.repo.structure import repo_structure
from tools.repo.summary import repo_summary

from tools.code.explain import explain_code

from tools.git.commits import recent_commits

from tools.docs.readme import generate_readme

mcp = FastMCP("AI-Codebase-MCP")


@mcp.tool()
def structure(repo_path: str):
    """Get repository file structure"""
    return repo_structure(repo_path)


@mcp.tool()
def summarize(repo_path: str):
    """Summarize repository"""
    return repo_summary(repo_path)


@mcp.tool()
def explain(file_path: str):
    """Explain code file"""
    return explain_code(file_path)


@mcp.tool()
def commits(repo_path: str):
    """Get recent git commits"""
    return recent_commits(repo_path)


@mcp.tool()
def readme(repo_path: str):
    """Generate README"""
    return generate_readme(repo_path)


if __name__ == "__main__":
    mcp.run()