"""
dependency_analyzer.py
-----------------------
Builds a project-wide JSON dependency graph by parsing import statements
across Python, Java, and JavaScript/TypeScript files.

Also parses package manifests (package.json, requirements.txt, pom.xml)
for external library dependencies.
"""

import os
import re
import json
from collections import defaultdict
from services.parser_service import get_all_files


# ---------------------------------------------------------------------------
# Language-specific import extractors
# ---------------------------------------------------------------------------

def _extract_python_imports(content: str, rel_path: str) -> list:
    """Extract Python import targets from file content."""
    imports = []
    # import X, import X as Y
    for m in re.finditer(r'^\s*import\s+([\w., ]+)', content, re.MULTILINE):
        for name in m.group(1).split(","):
            imports.append(name.strip().split(" as ")[0].strip())
    # from X import Y
    for m in re.finditer(r'^\s*from\s+([\w.]+)\s+import', content, re.MULTILINE):
        imports.append(m.group(1).strip())
    return imports


def _extract_java_imports(content: str, rel_path: str) -> list:
    """Extract Java import targets from file content."""
    imports = []
    for m in re.finditer(r'^\s*import\s+([\w.]+);', content, re.MULTILINE):
        imports.append(m.group(1).strip())
    return imports


def _extract_js_imports(content: str, rel_path: str) -> list:
    """Extract JS/TS import paths from file content."""
    imports = []
    # ES module: import X from 'path'
    for m in re.finditer(r"(?:import|export)\s+.*?from\s+['\"]([^'\"]+)['\"]", content, re.MULTILINE):
        imports.append(m.group(1).strip())
    # require('path')
    for m in re.finditer(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content):
        imports.append(m.group(1).strip())
    return imports


# ---------------------------------------------------------------------------
# Package manifest parsers for external dependencies
# ---------------------------------------------------------------------------

def _parse_package_json(repo_path: str) -> dict:
    package_path = os.path.join(repo_path, "package.json")
    if not os.path.exists(package_path):
        return {}
    try:
        with open(package_path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "dependencies": data.get("dependencies", {}),
            "devDependencies": data.get("devDependencies", {})
        }
    except Exception:
        return {}


def _parse_requirements_txt(repo_path: str) -> list:
    req_path = os.path.join(repo_path, "requirements.txt")
    if not os.path.exists(req_path):
        return []
    try:
        with open(req_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # strip version specifiers
                pkg = re.split(r'[>=<!~]', line)[0].strip()
                packages.append(pkg)
        return packages
    except Exception:
        return []


def _parse_pom_xml(repo_path: str) -> list:
    pom_path = os.path.join(repo_path, "pom.xml")
    if not os.path.exists(pom_path):
        return []
    try:
        with open(pom_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        deps = []
        for m in re.finditer(r'<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>', content, re.DOTALL):
            deps.append(f"{m.group(1).strip()}:{m.group(2).strip()}")
        return deps
    except Exception:
        return []


def _parse_pyproject_toml(repo_path: str) -> list:
    toml_path = os.path.join(repo_path, "pyproject.toml")
    if not os.path.exists(toml_path):
        return []
    try:
        with open(toml_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        # Basic parsing of dependencies list
        m = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if not m:
            return []
        raw = m.group(1)
        deps = [re.split(r'[>=<!~]', d.strip().strip('"').strip("'"))[0].strip()
                for d in raw.split(",") if d.strip()]
        return [d for d in deps if d]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Main graph builder
# ---------------------------------------------------------------------------

def analyze_dependencies(repo_path: str) -> str:
    """
    Scans all files and builds:
      1. A file-level internal dependency graph (imports between local files).
      2. Per-file external imports (library/package references).
      3. External package manifest summaries.
      4. Cycle detection in the internal dependency graph.

    Returns a JSON string representing the full dependency map.
    """
    files = get_all_files(repo_path)

    # Build a map of file_path -> set_of_imports
    file_imports: dict = {}  # rel_path -> list of import strings
    ext_map: dict = {}       # rel_path -> list of external imports

    for rel_path in files:
        full_path = os.path.join(repo_path, rel_path)
        _, ext = os.path.splitext(rel_path.lower())

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        if ext == ".py":
            raw_imports = _extract_python_imports(content, rel_path)
        elif ext == ".java":
            raw_imports = _extract_java_imports(content, rel_path)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            raw_imports = _extract_js_imports(content, rel_path)
        else:
            continue

        file_imports[rel_path] = raw_imports

    # Normalize internal file links
    # Build a short-name lookup for all files (basename without extension)
    file_set = set(files)
    file_base_map = {}  # base_module_name -> rel_path
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        file_base_map[base] = f
        # Also add the dotted module path for Python
        module_path = os.path.splitext(f)[0].replace(os.sep, ".")
        file_base_map[module_path] = f

    # Build internal (file -> file) and external edges
    graph = defaultdict(list)   # source -> list of target file paths (internal)
    external = defaultdict(list)  # source -> list of unresolved module strings

    for source_file, imports in file_imports.items():
        for imp in imports:
            resolved = None

            # Try exact match in file set
            for candidate in file_set:
                if imp in candidate or candidate.endswith(imp.replace(".", os.sep) + ".py") \
                        or candidate.endswith(imp.replace(".", os.sep) + ".java"):
                    resolved = candidate
                    break

            # Try base-name map
            if not resolved:
                resolved = file_base_map.get(imp) or file_base_map.get(imp.split(".")[-1])

            # Relative JS imports
            if not resolved and imp.startswith("."):
                dir_of_source = os.path.dirname(source_file)
                for ext_try in (".js", ".ts", ".jsx", ".tsx", "/index.js", "/index.ts"):
                    candidate = os.path.normpath(os.path.join(dir_of_source, imp + ext_try))
                    candidate = candidate.replace("\\", "/")
                    if candidate in [f.replace("\\", "/") for f in file_set]:
                        resolved = candidate
                        break

            if resolved and resolved != source_file:
                graph[source_file].append(resolved)
            else:
                external[source_file].append(imp)

    # Compute in-degree and out-degree
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    for src, targets in graph.items():
        out_degree[src] += len(targets)
        for tgt in targets:
            in_degree[tgt] += 1

    # Detect cycles using DFS
    def find_cycles(graph_dict):
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph_dict.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycles.append(path[cycle_start:] + [neighbor])
            rec_stack.discard(node)

        for node in list(graph_dict.keys()):
            if node not in visited:
                dfs(node, [node])
        return cycles[:10]  # return first 10 cycles max

    cycles = find_cycles(dict(graph))

    # External manifest packages
    npm_deps = _parse_package_json(repo_path)
    py_deps = _parse_requirements_txt(repo_path)
    java_deps = _parse_pom_xml(repo_path)
    toml_deps = _parse_pyproject_toml(repo_path)

    # Assemble the output graph
    output = {
        "summary": {
            "total_files_scanned": len(file_imports),
            "total_internal_links": sum(len(v) for v in graph.values()),
            "files_with_no_imports": [f for f in file_imports if f not in graph],
            "circular_dependencies": cycles
        },
        "internal_dependency_graph": {
            src: list(set(tgts)) for src, tgts in graph.items()
        },
        "file_metrics": {
            f: {
                "in_degree": in_degree.get(f, 0),
                "out_degree": out_degree.get(f, 0)
            }
            for f in set(list(in_degree.keys()) + list(out_degree.keys()))
        },
        "external_imports_by_file": {k: list(set(v)) for k, v in external.items() if v},
        "package_manifests": {
            "npm_dependencies": npm_deps.get("dependencies", {}),
            "npm_devDependencies": npm_deps.get("devDependencies", {}),
            "python_requirements_txt": py_deps,
            "python_pyproject_toml": toml_deps,
            "java_pom_xml": java_deps
        }
    }

    return json.dumps(output, indent=2)