"""
ast_service.py
--------------
Provides AST-based structural parsing for Python, Java, and JavaScript/TypeScript files.
- Python: uses the built-in `ast` module for accurate, structured extraction.
- Java / JS / TS: uses targeted regex patterns for structural extraction.
"""

import ast
import os
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Python AST Parsing
# ---------------------------------------------------------------------------

def parse_python_file(file_path: str):
    """
    Parses a Python file and returns a structured dict of all classes
    and top-level functions with their methods, parameters, bases, and docstrings.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return {"error": str(e)}

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}"}

    result = {"classes": [], "functions": []}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [_ast_name(b) for b in node.bases]
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                    methods.append({
                        "name": item.name,
                        "line": item.lineno,
                        "parameters": _extract_py_params(item),
                        "docstring": ast.get_docstring(item)
                    })
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "bases": bases,
                "docstring": ast.get_docstring(node),
                "methods": methods
            })

        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Only top-level functions (not inside a class)
            parent = _get_parent(tree, node)
            if isinstance(parent, ast.Module):
                result["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "parameters": _extract_py_params(node),
                    "docstring": ast.get_docstring(node)
                })

    return result


def _ast_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_ast_name(node.value)}.{node.attr}"
    return str(node)


def _extract_py_params(func_node) -> list:
    params = []
    args = func_node.args
    for arg in args.args:
        params.append(arg.arg)
    if args.vararg:
        params.append(f"*{args.vararg.arg}")
    for arg in args.kwonlyargs:
        params.append(arg.arg)
    if args.kwarg:
        params.append(f"**{args.kwarg.arg}")
    return params


def _get_parent(tree, target_node):
    """Find the direct parent of a node in the AST."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            if child is target_node:
                return node
    return None


# ---------------------------------------------------------------------------
# Java Structural Parsing (Regex-based)
# ---------------------------------------------------------------------------

def parse_java_file(file_path: str):
    """
    Uses structured regex patterns to extract classes, interfaces implemented,
    method signatures, and inheritance from a Java file.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return {"error": str(e)}

    result = {"classes": [], "interfaces": []}

    # Match class declarations: class MyClass extends Base implements A, B
    class_pattern = re.compile(
        r'(?:public|private|protected|abstract|final)?\s*class\s+(\w+)'
        r'(?:\s+extends\s+([\w<>, ]+?))?'
        r'(?:\s+implements\s+([\w<>, ]+?))?\s*\{',
        re.MULTILINE
    )
    # Match interface declarations
    iface_pattern = re.compile(
        r'(?:public|private|protected)?\s*interface\s+(\w+)'
        r'(?:\s+extends\s+([\w<>, ]+?))?\s*\{',
        re.MULTILINE
    )
    # Match method signatures inside a class body
    method_pattern = re.compile(
        r'(?:public|private|protected|static|final|abstract|synchronized|native|default|)\s*'
        r'(?:<[\w,\s?<>]+>\s+)?'   # generic return type
        r'([\w<>\[\]]+)\s+'         # return type
        r'(\w+)\s*'                 # method name
        r'\(([^)]*)\)\s*'           # parameters
        r'(?:throws\s+[\w, ]+)?\s*[{;]',
        re.MULTILINE
    )

    for m in class_pattern.finditer(source):
        class_name = m.group(1)
        extends = [x.strip() for x in m.group(2).split(",")] if m.group(2) else []
        implements = [x.strip() for x in m.group(3).split(",")] if m.group(3) else []
        line = source[:m.start()].count("\n") + 1

        methods = []
        for mm in method_pattern.finditer(source):
            mline = source[:mm.start()].count("\n") + 1
            if mline > line:  # rough scope: all methods after class start
                params_raw = mm.group(3).strip()
                params = [p.strip().split()[-1] for p in params_raw.split(",") if p.strip()] if params_raw else []
                methods.append({
                    "return_type": mm.group(1),
                    "name": mm.group(2),
                    "line": mline,
                    "parameters": params
                })

        result["classes"].append({
            "name": class_name,
            "line": line,
            "extends": extends,
            "implements": implements,
            "methods": methods[:30]  # limit to first 30
        })

    for m in iface_pattern.finditer(source):
        line = source[:m.start()].count("\n") + 1
        extends = [x.strip() for x in m.group(2).split(",")] if m.group(2) else []
        result["interfaces"].append({
            "name": m.group(1),
            "line": line,
            "extends": extends
        })

    return result


# ---------------------------------------------------------------------------
# JavaScript / TypeScript Structural Parsing (Regex-based)
# ---------------------------------------------------------------------------

def parse_js_file(file_path: str):
    """
    Extracts class names, extends/implements relationships, and method names
    from JavaScript or TypeScript files.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return {"error": str(e)}

    result = {"classes": [], "functions": []}

    # Match class declarations
    class_pattern = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+?))?\s*\{',
        re.MULTILINE
    )
    # Match method-like declarations inside a class
    method_pattern = re.compile(
        r'(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?'
        r'(\w+)\s*\(([^)]*)\)\s*(?::\s*[\w<>\[\]| ]+)?\s*\{',
        re.MULTILINE
    )
    # Top-level arrow functions or regular functions
    func_pattern = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
        re.MULTILINE
    )
    named_func_pattern = re.compile(
        r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        re.MULTILINE
    )

    for m in class_pattern.finditer(source):
        class_name = m.group(1)
        extends = m.group(2) if m.group(2) else None
        implements = [x.strip() for x in m.group(3).split(",")] if m.group(3) else []
        line = source[:m.start()].count("\n") + 1

        # Find methods in subsequent content
        class_body_start = m.end()
        methods = []
        for mm in method_pattern.finditer(source[class_body_start:class_body_start + 3000]):
            mname = mm.group(1)
            if mname not in ("if", "for", "while", "switch", "catch"):
                params_raw = mm.group(2).strip()
                params = [p.strip().split(":")[0].strip() for p in params_raw.split(",") if p.strip()]
                methods.append({
                    "name": mname,
                    "parameters": params,
                    "line": line + source[class_body_start:class_body_start + mm.start()].count("\n")
                })

        result["classes"].append({
            "name": class_name,
            "line": line,
            "extends": extends,
            "implements": implements,
            "methods": methods[:20]
        })

    for m in named_func_pattern.finditer(source):
        line = source[:m.start()].count("\n") + 1
        params_raw = m.group(2).strip()
        params = [p.strip().split(":")[0].strip() for p in params_raw.split(",") if p.strip()]
        result["functions"].append({
            "name": m.group(1),
            "line": line,
            "parameters": params
        })

    return result


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def parse_file(file_path: str) -> dict:
    """
    Parses any supported file type and returns a structural dict.
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".py":
        return parse_python_file(file_path)
    elif ext == ".java":
        return parse_java_file(file_path)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        return parse_js_file(file_path)
    else:
        return {"error": f"Unsupported file type: {ext}"}


# ---------------------------------------------------------------------------
# Structural Query Helpers
# ---------------------------------------------------------------------------

def find_classes_implementing(file_path: str, target: str) -> list:
    """
    Returns all classes in the file that extend or implement `target`.
    Works for Python (bases), Java (extends/implements), JS/TS (extends/implements).
    """
    parsed = parse_file(file_path)
    matches = []

    for cls in parsed.get("classes", []):
        # Python
        if target in cls.get("bases", []):
            matches.append(cls)
        # Java
        if target in cls.get("extends", []) or target in cls.get("implements", []):
            matches.append(cls)
        # JS/TS
        if cls.get("extends") == target or target in cls.get("implements", []):
            if cls not in matches:
                matches.append(cls)

    return matches


def extract_method_parameters(file_path: str, method_name: str) -> Optional[dict]:
    """
    Returns the parameters of the first method named `method_name` found across all classes.
    """
    parsed = parse_file(file_path)

    for cls in parsed.get("classes", []):
        for method in cls.get("methods", []):
            if method.get("name") == method_name:
                return {
                    "class": cls["name"],
                    "method": method_name,
                    "parameters": method.get("parameters", []),
                    "line": method.get("line")
                }

    for func in parsed.get("functions", []):
        if func.get("name") == method_name:
            return {
                "class": None,
                "method": method_name,
                "parameters": func.get("parameters", []),
                "line": func.get("line")
            }

    return None


def list_classes_and_methods(file_path: str) -> dict:
    """
    Returns a hierarchical listing of all classes/interfaces and their methods
    in the given file.
    """
    parsed = parse_file(file_path)
    return parsed
