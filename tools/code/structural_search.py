"""
structural_search.py
---------------------
Exposes AST-powered structural queries for the MCP server.
Allows the LLM to ask structural questions about code instead of grepping raw text.
"""

import os
import json
from services.ast_service import (
    parse_file,
    find_classes_implementing,
    extract_method_parameters,
    list_classes_and_methods
)
from services.parser_service import get_all_files


def ast_search(
    repo_path: str,
    query_type: str,
    target: str = "",
    file_filter: str = ""
) -> str:
    """
    Perform a structural AST-based query across the codebase.

    query_type options:
        "list_structure"         - Dump all classes and methods in a file (requires file_filter)
        "find_implementing"      - Find all classes that extend/implement `target`
        "get_method_params"      - Get the parameters of method named `target`
        "find_class"             - Find where class named `target` is defined

    Args:
        repo_path   : Path to the local repository.
        query_type  : One of the structural query types above.
        target      : Class name, interface name, or method name (depending on query_type).
        file_filter : Optional file path or extension filter (e.g. ".py", "src/models.py").

    Returns:
        A formatted string (JSON-rich) with the query results.
    """
    query_type = query_type.strip().lower()
    files = get_all_files(repo_path)

    # Apply optional file filter
    if file_filter:
        files = [f for f in files if file_filter in f]

    # -----------------------------------------------------------------------
    # list_structure: dump the full structural outline of a specific file
    # -----------------------------------------------------------------------
    if query_type == "list_structure":
        if not file_filter:
            return "Error: `list_structure` requires a `file_filter` to specify the file."

        matched_files = [f for f in files if file_filter in f]
        if not matched_files:
            return f"No file matching '{file_filter}' found in the repository."

        results = []
        for rel_path in matched_files[:3]:
            full_path = os.path.join(repo_path, rel_path)
            parsed = list_classes_and_methods(full_path)
            results.append({"file": rel_path, "structure": parsed})

        return json.dumps(results, indent=2)

    # -----------------------------------------------------------------------
    # find_implementing: find all classes that extend or implement `target`
    # -----------------------------------------------------------------------
    elif query_type == "find_implementing":
        if not target:
            return "Error: `find_implementing` requires a `target` (class or interface name)."

        matches = []
        for rel_path in files:
            full_path = os.path.join(repo_path, rel_path)
            try:
                hits = find_classes_implementing(full_path, target)
                for cls in hits:
                    matches.append({"file": rel_path, "class": cls})
            except Exception:
                continue

        if not matches:
            return f"No classes found that implement or extend '{target}'."

        return json.dumps(matches, indent=2)

    # -----------------------------------------------------------------------
    # get_method_params: extract parameters of a named method/function
    # -----------------------------------------------------------------------
    elif query_type == "get_method_params":
        if not target:
            return "Error: `get_method_params` requires a `target` (method or function name)."

        matches = []
        for rel_path in files:
            full_path = os.path.join(repo_path, rel_path)
            try:
                result = extract_method_parameters(full_path, target)
                if result:
                    result["file"] = rel_path
                    matches.append(result)
            except Exception:
                continue

        if not matches:
            return f"Method or function '{target}' not found in the codebase."

        return json.dumps(matches, indent=2)

    # -----------------------------------------------------------------------
    # find_class: locate where a class is defined
    # -----------------------------------------------------------------------
    elif query_type == "find_class":
        if not target:
            return "Error: `find_class` requires a `target` (class name)."

        matches = []
        for rel_path in files:
            full_path = os.path.join(repo_path, rel_path)
            try:
                parsed = parse_file(full_path)
                for cls in parsed.get("classes", []):
                    if cls.get("name") == target:
                        matches.append({
                            "file": rel_path,
                            "line": cls.get("line"),
                            "bases": cls.get("bases", []) or cls.get("extends", []),
                            "implements": cls.get("implements", []),
                            "methods": [m.get("name") for m in cls.get("methods", [])]
                        })
            except Exception:
                continue

        if not matches:
            return f"Class '{target}' not found in the codebase."

        return json.dumps(matches, indent=2)

    else:
        return (
            f"Unknown query_type: '{query_type}'.\n"
            "Valid options: list_structure | find_implementing | get_method_params | find_class"
        )
