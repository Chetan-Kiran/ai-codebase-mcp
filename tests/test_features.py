"""
tests/test_features.py
------------------------
Integration and unit tests for all five upgraded features.

Run with:
    python -m pytest tests/test_features.py -v
"""

import os
import sys
import json
import shutil
import tempfile
import unittest

# Add project root to sys.path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ===========================================================================
# Fixtures — sample source files
# ===========================================================================

SAMPLE_PYTHON = '''
class Animal:
    """Base animal class."""
    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        raise NotImplementedError


class Dog(Animal):
    """A dog that barks."""
    def speak(self) -> str:
        return f"{self.name} says woof!"


def standalone_function(x: int, y: int) -> int:
    """Returns the sum of x and y."""
    return x + y
'''

SAMPLE_JAVA = '''
package com.example;

import java.util.List;
import java.io.IOException;

public class UserService implements IUserService, Serializable {
    private UserRepository repo;

    public UserService(UserRepository repo) {
        this.repo = repo;
    }

    public List<User> getUsers() throws IOException {
        return repo.findAll();
    }

    private void validateUser(User user) {
        // validation logic
    }
}

interface IUserService {
    List<User> getUsers() throws IOException;
}
'''

SAMPLE_JS = '''
export class EventEmitter extends BaseEmitter implements IEmitter {
    constructor(options) {
        super(options);
    }

    emit(event, data) {
        this.listeners[event]?.forEach(fn => fn(data));
    }

    on(event, handler) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(handler);
    }
}

export function createEmitter(options) {
    return new EventEmitter(options);
}
'''

SAMPLE_IMPORTER_PY = '''
from services.indexer_service import search_repo
from tools.code.structural_search import ast_search
import os
import json
'''


# ===========================================================================
# Test 1: AST Service — Python
# ===========================================================================

class TestAstServicePython(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.py_file = os.path.join(self.tmp_dir, "sample.py")
        with open(self.py_file, "w") as f:
            f.write(SAMPLE_PYTHON)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_parse_classes(self):
        from services.ast_service import parse_python_file
        result = parse_python_file(self.py_file)
        class_names = [c["name"] for c in result["classes"]]
        self.assertIn("Animal", class_names)
        self.assertIn("Dog", class_names)

    def test_class_bases(self):
        from services.ast_service import parse_python_file
        result = parse_python_file(self.py_file)
        dog = next(c for c in result["classes"] if c["name"] == "Dog")
        self.assertIn("Animal", dog["bases"])

    def test_method_params(self):
        from services.ast_service import extract_method_parameters
        result = extract_method_parameters(self.py_file, "standalone_function")
        self.assertIsNotNone(result)
        self.assertIn("x", result["parameters"])
        self.assertIn("y", result["parameters"])

    def test_find_implementing(self):
        from services.ast_service import find_classes_implementing
        result = find_classes_implementing(self.py_file, "Animal")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]["name"], "Dog")

    def test_top_level_functions(self):
        from services.ast_service import parse_python_file
        result = parse_python_file(self.py_file)
        func_names = [f["name"] for f in result["functions"]]
        self.assertIn("standalone_function", func_names)


# ===========================================================================
# Test 2: AST Service — Java
# ===========================================================================

class TestAstServiceJava(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.java_file = os.path.join(self.tmp_dir, "UserService.java")
        with open(self.java_file, "w") as f:
            f.write(SAMPLE_JAVA)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_parse_java_class(self):
        from services.ast_service import parse_java_file
        result = parse_java_file(self.java_file)
        class_names = [c["name"] for c in result["classes"]]
        self.assertIn("UserService", class_names)

    def test_java_implements(self):
        from services.ast_service import parse_java_file
        result = parse_java_file(self.java_file)
        user_svc = next(c for c in result["classes"] if c["name"] == "UserService")
        self.assertIn("IUserService", user_svc["implements"])

    def test_java_interfaces(self):
        from services.ast_service import parse_java_file
        result = parse_java_file(self.java_file)
        iface_names = [i["name"] for i in result["interfaces"]]
        self.assertIn("IUserService", iface_names)


# ===========================================================================
# Test 3: AST Service — JavaScript
# ===========================================================================

class TestAstServiceJS(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.js_file = os.path.join(self.tmp_dir, "emitter.js")
        with open(self.js_file, "w") as f:
            f.write(SAMPLE_JS)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_parse_js_class(self):
        from services.ast_service import parse_js_file
        result = parse_js_file(self.js_file)
        class_names = [c["name"] for c in result["classes"]]
        self.assertIn("EventEmitter", class_names)

    def test_js_extends(self):
        from services.ast_service import parse_js_file
        result = parse_js_file(self.js_file)
        emitter = next(c for c in result["classes"] if c["name"] == "EventEmitter")
        self.assertEqual(emitter["extends"], "BaseEmitter")


# ===========================================================================
# Test 4: Structural Search Tool
# ===========================================================================

class TestStructuralSearch(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        # Create a fake parser service IGNORE_DIRS set up
        py_file = os.path.join(self.tmp_dir, "models.py")
        with open(py_file, "w") as f:
            f.write(SAMPLE_PYTHON)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_list_structure(self):
        from tools.code.structural_search import ast_search
        result = ast_search(self.tmp_dir, "list_structure", file_filter="models.py")
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_find_implementing(self):
        from tools.code.structural_search import ast_search
        result = ast_search(self.tmp_dir, "find_implementing", target="Animal")
        data = json.loads(result)
        self.assertIsInstance(data, list)
        found_names = [d["class"]["name"] for d in data]
        self.assertIn("Dog", found_names)

    def test_get_method_params(self):
        from tools.code.structural_search import ast_search
        result = ast_search(self.tmp_dir, "get_method_params", target="standalone_function")
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        self.assertIn("x", data[0]["parameters"])

    def test_find_class(self):
        from tools.code.structural_search import ast_search
        result = ast_search(self.tmp_dir, "find_class", target="Dog")
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)


# ===========================================================================
# Test 5: Dependency Graph
# ===========================================================================

class TestDependencyGraph(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        # Create interconnected files
        file_a = os.path.join(self.tmp_dir, "module_a.py")
        file_b = os.path.join(self.tmp_dir, "module_b.py")
        file_c = os.path.join(self.tmp_dir, "module_c.py")

        with open(file_a, "w") as f:
            f.write("import module_b\nimport os\n\nclass A:\n    pass\n")
        with open(file_b, "w") as f:
            f.write("import module_c\n\nclass B:\n    pass\n")
        with open(file_c, "w") as f:
            f.write("# Standalone module\nclass C:\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_graph_produces_json(self):
        from tools.repo.dependency_analyzer import analyze_dependencies
        result = analyze_dependencies(self.tmp_dir)
        data = json.loads(result)
        self.assertIn("summary", data)
        self.assertIn("internal_dependency_graph", data)

    def test_internal_links_detected(self):
        from tools.repo.dependency_analyzer import analyze_dependencies
        result = analyze_dependencies(self.tmp_dir)
        data = json.loads(result)
        self.assertGreater(data["summary"]["total_internal_links"], 0)

    def test_summary_has_file_count(self):
        from tools.repo.dependency_analyzer import analyze_dependencies
        result = analyze_dependencies(self.tmp_dir)
        data = json.loads(result)
        self.assertGreater(data["summary"]["total_files_scanned"], 0)


# ===========================================================================
# Test 6: Refactoring Sandbox
# ===========================================================================

class TestSandboxRefactor(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.py_file = "sample.py"
        full = os.path.join(self.tmp_dir, self.py_file)
        with open(full, "w") as f:
            f.write(SAMPLE_PYTHON)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_valid_full_file_replacement(self):
        from tools.code.refactor import sandbox_refactor
        new_code = "# Replaced\nclass Empty:\n    pass\n"
        result = sandbox_refactor(self.tmp_dir, self.py_file, "full_file", "", new_code)
        self.assertIn("✅ SANDBOX APPROVED", result)

        # Verify the file was actually updated
        full = os.path.join(self.tmp_dir, self.py_file)
        with open(full) as f:
            content = f.read()
        self.assertIn("class Empty", content)

    def test_invalid_syntax_rejected(self):
        from tools.code.refactor import sandbox_refactor
        bad_code = "def broken_function(\n    # missing close paren and body\n"
        result = sandbox_refactor(self.tmp_dir, self.py_file, "full_file", "", bad_code)
        self.assertIn("❌ SANDBOX REJECTED", result)

        # Verify the original file is UNTOUCHED
        full = os.path.join(self.tmp_dir, self.py_file)
        with open(full) as f:
            content = f.read()
        self.assertIn("class Animal", content)

    def test_line_range_replacement(self):
        from tools.code.refactor import sandbox_refactor
        # Replace lines 17-20 (the standalone_function block) with a new valid function.
        # These lines form a self-contained unit so replacement won't break surrounding syntax.
        new_code = "def standalone_function(x: int, y: int) -> int:\n    return x * y\n"
        result = sandbox_refactor(self.tmp_dir, self.py_file, "lines", "17,20", new_code)
        self.assertIn("✅ SANDBOX APPROVED", result)

    def test_method_replacement_python(self):
        from tools.code.refactor import sandbox_refactor
        new_speak = "    def speak(self) -> str:\n        return 'woof woof!'\n"
        result = sandbox_refactor(self.tmp_dir, self.py_file, "method", "speak", new_speak)
        self.assertIn("✅ SANDBOX APPROVED", result)

    def test_file_not_found(self):
        from tools.code.refactor import sandbox_refactor
        result = sandbox_refactor(self.tmp_dir, "nonexistent.py", "full_file", "", "x = 1")
        self.assertIn("❌ File not found", result)


# ===========================================================================
# Test 7: Vector Search (lightweight — skip if deps missing)
# ===========================================================================

class TestVectorSearch(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        py_file = os.path.join(self.tmp_dir, "code.py")
        with open(py_file, "w") as f:
            f.write(SAMPLE_PYTHON)
        # Patch the DB and FAISS paths to live in temp dir
        import services.indexer_service as idx
        self._orig_db = idx.DB_PATH
        self._orig_faiss = idx.FAISS_INDEX_PATH
        idx.DB_PATH = os.path.join(self.tmp_dir, "test.db")
        idx.FAISS_INDEX_PATH = os.path.join(self.tmp_dir, "test.faiss")

    def tearDown(self):
        import services.indexer_service as idx
        idx.DB_PATH = self._orig_db
        idx.FAISS_INDEX_PATH = self._orig_faiss
        shutil.rmtree(self.tmp_dir)

    def test_indexing_and_search(self):
        try:
            from services.indexer_service import index_repo, search_repo
        except ImportError:
            self.skipTest("sentence-transformers or faiss not installed")

        index_repo(self.tmp_dir)
        results = search_repo(self.tmp_dir, "animal speak method", top_k=3)
        self.assertIsInstance(results, list)
        # At least one result back
        self.assertGreater(len(results), 0)
        # Each result has expected keys
        for r in results:
            self.assertIn("file_path", r)
            self.assertIn("content", r)
            self.assertIn("score", r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
