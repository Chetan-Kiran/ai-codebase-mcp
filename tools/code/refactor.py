"""
refactor.py
-----------
Provides two interfaces:

1. rewrite_code(code, instructions)
   - Classic: rewrites a code snippet using the LLM (unchanged behaviour).

2. sandbox_refactor(repo_path, file_path, target_type, target, new_code)
   - Transactional refactoring sandbox.
   - Copies the file to a temp location, applies the change, validates syntax,
     and only commits if it passes — otherwise aborts and reports the error.
"""

import os
import ast
import shutil
import tempfile
import re
from services.llm_service import ask_llm


# ---------------------------------------------------------------------------
# Classic rewrite (unchanged)
# ---------------------------------------------------------------------------

def rewrite_code(code, instructions="Refactor this code to be cleaner and more efficient."):
    """
    Rewrites code based on provided instructions using the LLM.
    No sandbox — operates purely on a code snippet string.
    """
    prompt = f"""
Input Code:
```
{code}
```

Instructions: {instructions}

Please rewrite the code according to the instructions. Provide only the code in your response, without any explanations or markdown blocks.
"""
    return ask_llm(prompt)


def remove_dead_code(code):
    """
    Specific helper to remove dead code from a snippet.
    """
    return rewrite_code(
        code,
        "Identify and remove any dead code, unused variables, or unreachable logic from this code."
    )


# ---------------------------------------------------------------------------
# Syntax validation helpers
# ---------------------------------------------------------------------------

def _validate_python(source: str) -> tuple:
    """Returns (is_valid: bool, error_message: str)."""
    try:
        compile(source, "<sandbox>", "exec")
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def _validate_java(source: str) -> tuple:
    """Basic Java structure validation (brace balance + class presence)."""
    open_braces = source.count("{")
    close_braces = source.count("}")
    if open_braces != close_braces:
        return False, f"Unbalanced braces: {open_braces} open vs {close_braces} close."
    if "class " not in source and "interface " not in source:
        return False, "No class or interface declaration found."
    return True, ""


def _validate_js(source: str) -> tuple:
    """Basic JS/TS structure validation (brace balance)."""
    open_braces = source.count("{")
    close_braces = source.count("}")
    if open_braces != close_braces:
        return False, f"Unbalanced braces: {open_braces} open vs {close_braces} close."
    return True, ""


def _validate_source(source: str, extension: str) -> tuple:
    ext = extension.lower()
    if ext == ".py":
        return _validate_python(source)
    elif ext == ".java":
        return _validate_java(source)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        return _validate_js(source)
    else:
        # No validation available — pass through
        return True, ""


# ---------------------------------------------------------------------------
# Target block replacement helpers
# ---------------------------------------------------------------------------

def _replace_by_lines(source_lines: list, start_line: int, end_line: int, new_code: str) -> list:
    """Replace a line range (1-indexed, inclusive) with new_code lines."""
    new_lines = new_code.splitlines(keepends=True)
    return source_lines[:start_line - 1] + new_lines + source_lines[end_line:]


def _replace_method_python(source: str, method_name: str, new_code: str) -> str:
    """
    Finds the first Python function/method named `method_name` and replaces its body.
    Preserves the rest of the file.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source  # Can't parse — return unchanged

    lines = source.splitlines(keepends=True)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == method_name:
                start = node.lineno - 1
                end = node.end_lineno  # exclusive in slice

                new_lines = new_code.splitlines(keepends=True)
                return "".join(lines[:start] + new_lines + lines[end:])

    return source  # method not found


def _replace_method_regex(source: str, method_name: str, new_code: str, ext: str) -> str:
    """
    For Java/JS: finds the method block by name using brace-counting and replaces it.
    """
    # Find the method header
    pattern = re.compile(
        rf'((?:public|private|protected|static|async|final|override)?\s*)'
        rf'(\w[\w<>\[\]]*\s+)?'  # return type or async
        rf'({re.escape(method_name)})\s*\([^)]*\)\s*(?:throws\s+[\w, ]+)?\s*\{{',
        re.MULTILINE
    )
    m = pattern.search(source)
    if not m:
        return source

    start_pos = m.start()
    brace_pos = m.end() - 1  # position of opening '{'

    # Count braces to find the matching close brace
    depth = 0
    i = brace_pos
    while i < len(source):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break
        i += 1
    else:
        return source  # couldn't find matching brace

    return source[:start_pos] + new_code + source[end_pos:]


# ---------------------------------------------------------------------------
# Sandbox refactoring (transactional)
# ---------------------------------------------------------------------------

def sandbox_refactor(
    repo_path: str,
    file_path: str,
    target_type: str,
    target: str,
    new_code: str
) -> str:
    """
    Transactional, safe code modification tool.

    Args:
        repo_path   : Absolute path to the repository root.
        file_path   : Relative path to the file inside the repo.
        target_type : One of "lines", "method", "full_file".
        target      : For "lines": "start_line,end_line" (e.g. "10,25").
                      For "method": the method/function name.
                      For "full_file": ignored.
        new_code    : The replacement code string.

    Workflow:
        1. Copies the target file to a temp sandbox location.
        2. Applies the change to the copy.
        3. Validates syntax (Python: ast.parse / compile; Java/JS: structural check).
        4. If valid → overwrites original file. Returns success + diff summary.
        5. If invalid → discards temp, returns the error for the caller to fix.
    """
    full_path = os.path.join(repo_path, file_path)

    if not os.path.exists(full_path):
        return f"❌ File not found: {file_path}"

    _, ext = os.path.splitext(file_path)

    # Step 1: Read original content
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            original_source = f.read()
    except Exception as e:
        return f"❌ Could not read file: {e}"

    original_lines = original_source.splitlines(keepends=True)

    # Step 2: Apply the change to a copy
    try:
        target_type = target_type.strip().lower()

        if target_type == "full_file":
            modified_source = new_code

        elif target_type == "lines":
            parts = target.split(",")
            if len(parts) != 2:
                return "❌ For target_type='lines', target must be 'start_line,end_line' e.g. '10,25'."
            start_line = int(parts[0].strip())
            end_line = int(parts[1].strip())
            modified_lines = _replace_by_lines(original_lines, start_line, end_line, new_code)
            modified_source = "".join(modified_lines)

        elif target_type == "method":
            if not target:
                return "❌ For target_type='method', provide the method name in `target`."
            if ext == ".py":
                modified_source = _replace_method_python(original_source, target, new_code)
            elif ext in (".java", ".js", ".ts", ".jsx", ".tsx"):
                modified_source = _replace_method_regex(original_source, target, new_code, ext)
            else:
                return f"❌ Method-level replacement not supported for '{ext}' files."

            if modified_source == original_source:
                return f"⚠️  Method '{target}' not found in {file_path}. No changes made."

        else:
            return f"❌ Unknown target_type: '{target_type}'. Use: lines | method | full_file"

    except ValueError as e:
        return f"❌ Target parsing error: {e}"

    # Step 3: Write to temp file and validate
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
            tmp_f.write(modified_source)

        is_valid, error_msg = _validate_source(modified_source, ext)

        if not is_valid:
            return (
                f"❌ SANDBOX REJECTED — Syntax validation failed. No changes applied to '{file_path}'.\n"
                f"Error: {error_msg}\n\n"
                f"Please fix the new_code and retry."
            )

        # Step 4: Commit — overwrite original file
        shutil.copy2(tmp_path, full_path)

    finally:
        # Step 5: Always clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Summary
    original_line_count = len(original_lines)
    new_line_count = len(modified_source.splitlines())
    delta = new_line_count - original_line_count

    return (
        f"✅ SANDBOX APPROVED — Change committed to '{file_path}'.\n"
        f"  target_type : {target_type}\n"
        f"  target      : {target or '(full file)'}\n"
        f"  lines before: {original_line_count}\n"
        f"  lines after : {new_line_count} ({'+' if delta >= 0 else ''}{delta})\n"
        f"  validation  : passed ({ext} syntax check)"
    )
