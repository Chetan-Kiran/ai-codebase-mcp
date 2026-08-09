"""
change_impact.py
-----------------
Analyses uncommitted git changes (staged + unstaged) in a local repository and
predicts what may break by mapping changed line ranges against the AST and the
dependency graph.

Uses:
  - GitPython  -> diff extraction
  - ast_service -> structural mapping of changed lines to class/method definitions
  - dependency_analyzer -> cross-file impact propagation
"""

import os
import re
import json
from collections import defaultdict

from git import Repo, InvalidGitRepositoryError
from services.ast_service import parse_file
from services.parser_service import get_all_files


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _get_repo(repo_path: str) -> Repo:
    try:
        return Repo(repo_path)
    except InvalidGitRepositoryError:
        raise ValueError(f"'{repo_path}' is not a valid git repository.")


def _get_diff_hunks(repo: Repo) -> list:
    """
    Returns a list of changed hunks across both staged and unstaged diffs.
    Each entry: {"file": relative_path, "start_line": int, "end_line": int, "change_type": str}
    """
    hunks = []
    line_range_pat = re.compile(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')

    def process_diff(diff_index):
        for diff in diff_index:
            try:
                a_path = diff.a_path or ""
                b_path = diff.b_path or ""
                rel_path = b_path if b_path else a_path
                change_type = diff.change_type  # 'A', 'D', 'M', 'R'

                diff_text = ""
                try:
                    if diff.diff:
                        diff_text = diff.diff.decode("utf-8", errors="ignore")
                except Exception:
                    pass

                for m in line_range_pat.finditer(diff_text):
                    start = int(m.group(1))
                    count = int(m.group(2)) if m.group(2) is not None else 1
                    end = start + max(count - 1, 0)
                    hunks.append({
                        "file": rel_path,
                        "start_line": start,
                        "end_line": end,
                        "change_type": change_type
                    })
            except Exception:
                continue

    # Staged changes (HEAD → index)
    try:
        process_diff(repo.index.diff("HEAD"))
    except Exception:
        pass

    # Unstaged changes (index → working tree)
    try:
        process_diff(repo.index.diff(None))
    except Exception:
        pass

    return hunks


def _get_untracked_files(repo: Repo) -> list:
    """Returns a list of untracked new files."""
    try:
        return repo.untracked_files
    except Exception:
        return []


# ---------------------------------------------------------------------------
# AST mapping: changed lines → structural units
# ---------------------------------------------------------------------------

def _map_lines_to_structures(file_path: str, start_line: int, end_line: int) -> dict:
    """
    Given a file path and a changed line range, returns which classes/methods
    overlap with those lines.
    """
    if not os.path.exists(file_path):
        return {}

    parsed = parse_file(file_path)
    affected = {"classes": [], "methods": []}

    def lines_overlap(node_line, range_start, range_end):
        # Approximate: consider it touched if within 10 lines
        return range_start - 5 <= node_line <= range_end + 5

    for cls in parsed.get("classes", []):
        cls_line = cls.get("line", 0)
        if lines_overlap(cls_line, start_line, end_line):
            affected["classes"].append(cls.get("name"))

        for method in cls.get("methods", []):
            m_line = method.get("line", 0)
            if lines_overlap(m_line, start_line, end_line):
                affected["methods"].append(f"{cls.get('name')}.{method.get('name')}")

    for func in parsed.get("functions", []):
        if lines_overlap(func.get("line", 0), start_line, end_line):
            affected["methods"].append(func.get("name"))

    return affected


# ---------------------------------------------------------------------------
# Dependency propagation
# ---------------------------------------------------------------------------

def _build_reverse_dependency_map(repo_path: str, files: list) -> dict:
    """
    Builds a reverse map: file -> list of files that import it.
    Quick local parse without calling the full dependency_analyzer.
    """
    reverse_map = defaultdict(list)
    file_set = set(files)
    file_base_map = {}

    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        file_base_map[base] = f
        mod = os.path.splitext(f)[0].replace(os.sep, ".")
        file_base_map[mod] = f

    import_patterns = {
        ".py": [re.compile(r'^\s*import\s+([\w., ]+)', re.MULTILINE),
                re.compile(r'^\s*from\s+([\w.]+)\s+import', re.MULTILINE)],
        ".java": [re.compile(r'^\s*import\s+([\w.]+);', re.MULTILINE)],
        ".js": [re.compile(r"from\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
                re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", re.MULTILINE)],
    }
    import_patterns[".ts"] = import_patterns[".js"]
    import_patterns[".tsx"] = import_patterns[".js"]
    import_patterns[".jsx"] = import_patterns[".js"]

    for rel_path in files:
        full_path = os.path.join(repo_path, rel_path)
        _, ext = os.path.splitext(rel_path.lower())
        patterns = import_patterns.get(ext, [])
        if not patterns:
            continue

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        for pattern in patterns:
            for m in pattern.finditer(content):
                imp = m.group(1).strip()
                for imp_part in imp.split(","):
                    imp_part = imp_part.strip().split(" as ")[0].strip()
                    resolved = file_base_map.get(imp_part) or file_base_map.get(imp_part.split(".")[-1])
                    if resolved and resolved != rel_path:
                        reverse_map[resolved].append(rel_path)

    return dict(reverse_map)


def _propagate_impact(changed_files: list, reverse_map: dict, depth: int = 2) -> dict:
    """
    Given a set of changed files, walks up the reverse dependency graph to find
    all files that might be indirectly affected (up to `depth` hops).
    """
    direct = set()
    indirect = set()

    for f in changed_files:
        for importer in reverse_map.get(f, []):
            direct.add(importer)

    if depth > 1:
        for f in list(direct):
            for importer in reverse_map.get(f, []):
                if importer not in direct and importer not in changed_files:
                    indirect.add(importer)

    return {
        "direct_impact": sorted(direct),
        "indirect_impact": sorted(indirect - direct)
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_change_impact(repo_path: str) -> str:
    """
    Analyses uncommitted git changes and predicts structural impact.
    Returns a JSON-formatted report.
    """
    repo = _get_repo(repo_path)
    all_files = get_all_files(repo_path)
    hunks = _get_diff_hunks(repo)
    untracked = _get_untracked_files(repo)

    if not hunks and not untracked:
        return json.dumps({
            "status": "clean",
            "message": "No uncommitted changes found.",
            "untracked_files": untracked
        }, indent=2)

    # Map each changed hunk to structural units
    changed_file_details = defaultdict(lambda: {
        "change_type": "M",
        "hunks": [],
        "affected_classes": set(),
        "affected_methods": set()
    })

    for hunk in hunks:
        rel_file = hunk["file"]
        full_path = os.path.join(repo_path, rel_file)
        changed_file_details[rel_file]["change_type"] = hunk["change_type"]
        changed_file_details[rel_file]["hunks"].append({
            "lines": f"{hunk['start_line']}-{hunk['end_line']}"
        })

        structures = _map_lines_to_structures(full_path, hunk["start_line"], hunk["end_line"])
        changed_file_details[rel_file]["affected_classes"].update(structures.get("classes", []))
        changed_file_details[rel_file]["affected_methods"].update(structures.get("methods", []))

    # Serialize sets to lists
    for v in changed_file_details.values():
        v["affected_classes"] = sorted(v["affected_classes"])
        v["affected_methods"] = sorted(v["affected_methods"])

    # Build reverse dependency map and propagate impact
    reverse_map = _build_reverse_dependency_map(repo_path, all_files)
    changed_files_list = list(changed_file_details.keys())
    impact = _propagate_impact(changed_files_list, reverse_map)

    # Compute safety score (simple heuristic)
    total_impact = len(impact["direct_impact"]) + len(impact["indirect_impact"])
    if total_impact == 0:
        safety = "✅ LOW RISK — Changes appear to be self-contained."
    elif total_impact < 5:
        safety = "⚠️  MEDIUM RISK — A few files depend on changed code. Review them."
    else:
        safety = "🚨 HIGH RISK — Many files are potentially impacted. Run tests before merging."

    report = {
        "status": "changes_detected",
        "safety_assessment": safety,
        "changed_files": dict(changed_file_details),
        "untracked_files": untracked,
        "dependency_impact": impact,
        "recommendations": _build_recommendations(changed_file_details, impact)
    }

    return json.dumps(report, indent=2)


def _build_recommendations(changed_details: dict, impact: dict) -> list:
    recs = []

    for file, details in changed_details.items():
        if details["affected_methods"]:
            recs.append(
                f"Review callers of: {', '.join(details['affected_methods'])} (modified in {file})"
            )

    if impact["direct_impact"]:
        recs.append(
            f"Run tests for directly affected files: {', '.join(impact['direct_impact'][:5])}"
        )

    if impact["indirect_impact"]:
        recs.append(
            f"Audit transitively affected files: {', '.join(impact['indirect_impact'][:5])}"
        )

    if not recs:
        recs.append("No cross-file impact detected. Change appears isolated.")

    return recs
