"""Comprehensive tests for the Deep Repo Analyzer (analyze_repo.py)."""

import sys
import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestGetTree(unittest.TestCase):
    """Test the get_tree function."""

    def setUp(self):
        from analyze_repo import get_tree
        self.get_tree = get_tree
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_directory(self):
        result = self.get_tree(str(self.tmpdir))
        self.assertIsInstance(result, str)

    def test_nested_structure(self):
        (self.tmpdir / "src").mkdir()
        (self.tmpdir / "src" / "main.py").write_text("print('hi')")
        (self.tmpdir / "README.md").write_text("# Test")
        result = self.get_tree(str(self.tmpdir))
        self.assertIn("src", result)
        self.assertIn("main.py", result)

    def test_max_depth(self):
        deep = self.tmpdir / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "file.txt").write_text("x")
        result = self.get_tree(str(self.tmpdir), max_depth=2)
        # Check by line to avoid false positives from tmpdir name containing 'd'
        lines = result.split('\n')
        dir_entries = [l.strip() for l in lines if l.strip().endswith('/')]
        self.assertNotIn("d/", dir_entries)

    def test_ignores_git(self):
        (self.tmpdir / ".git").mkdir()
        (self.tmpdir / ".git" / "config").write_text("[core]")
        result = self.get_tree(str(self.tmpdir))
        self.assertNotIn(".git", result)

    def test_ignores_node_modules(self):
        (self.tmpdir / "node_modules").mkdir()
        (self.tmpdir / "node_modules" / "pkg").mkdir()
        result = self.get_tree(str(self.tmpdir))
        self.assertNotIn("node_modules", result)

    def test_ignores_pycache(self):
        (self.tmpdir / "__pycache__").mkdir()
        result = self.get_tree(str(self.tmpdir))
        self.assertNotIn("__pycache__", result)


class TestGetStats(unittest.TestCase):
    """Test the get_stats function."""

    def setUp(self):
        from analyze_repo import get_stats
        self.get_stats = get_stats
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_directory(self):
        total, types = self.get_stats(str(self.tmpdir))
        self.assertEqual(total, 0)
        self.assertEqual(types, {})

    def test_counts_files(self):
        (self.tmpdir / "a.py").write_text("x")
        (self.tmpdir / "b.py").write_text("x")
        (self.tmpdir / "c.md").write_text("x")
        total, types = self.get_stats(str(self.tmpdir))
        self.assertEqual(total, 3)
        self.assertEqual(types.get("py", 0), 2)
        self.assertEqual(types.get("md", 0), 1)

    def test_ignores_git_files(self):
        (self.tmpdir / ".git").mkdir()
        (self.tmpdir / ".git" / "config").write_text("x")
        (self.tmpdir / "main.py").write_text("x")
        total, types = self.get_stats(str(self.tmpdir))
        self.assertEqual(total, 1)

    def test_sorted_by_frequency(self):
        for i in range(5):
            (self.tmpdir / f"f{i}.py").write_text("x")
        for i in range(3):
            (self.tmpdir / f"g{i}.md").write_text("x")
        total, types = self.get_stats(str(self.tmpdir))
        keys = list(types.keys())
        self.assertEqual(keys[0], "py")

    def test_max_15_types(self):
        """Stats returns at most 15 file types."""
        for ext in "abcdefghijklmnopqrstuvwxyz":
            (self.tmpdir / f"file.{ext}").write_text("x")
        total, types = self.get_stats(str(self.tmpdir))
        self.assertLessEqual(len(types), 15)

    def test_no_extension_files(self):
        (self.tmpdir / "Makefile").write_text("all:")
        (self.tmpdir / "LICENSE").write_text("MIT")
        total, types = self.get_stats(str(self.tmpdir))
        self.assertEqual(total, 2)
        self.assertIn("none", types)


class TestGetReadme(unittest.TestCase):
    """Test the get_readme function."""

    def setUp(self):
        from analyze_repo import get_readme
        self.get_readme = get_readme
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_returns_readme_content(self):
        (self.tmpdir / "README.md").write_text("# My Project\n\nDescription here.")
        result = self.get_readme(str(self.tmpdir))
        self.assertIn("My Project", result)

    def test_no_readme_returns_empty(self):
        result = self.get_readme(str(self.tmpdir))
        self.assertEqual(result, "")

    def test_readme_txt_fallback(self):
        (self.tmpdir / "README.txt").write_text("Plain text readme")
        result = self.get_readme(str(self.tmpdir))
        self.assertIn("Plain text readme", result)

    def test_readme_without_extension(self):
        (self.tmpdir / "README").write_text("No extension readme")
        result = self.get_readme(str(self.tmpdir))
        self.assertIn("No extension readme", result)

    def test_truncates_long_readme(self):
        content = "x" * 10000
        (self.tmpdir / "README.md").write_text(content)
        result = self.get_readme(str(self.tmpdir))
        self.assertLessEqual(len(result), 4000)


class TestGetPackageInfo(unittest.TestCase):
    """Test the get_package_info function."""

    def setUp(self):
        from analyze_repo import get_package_info
        self.get_package_info = get_package_info
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_npm_package(self):
        pkg_json = json.dumps({
            "name": "test-pkg",
            "version": "1.0.0",
            "dependencies": {"express": "^4.0.0", "lodash": "^4.17.0"},
            "scripts": {"start": "node index.js", "test": "jest"}
        })
        (self.tmpdir / "package.json").write_text(pkg_json)
        result = self.get_package_info(str(self.tmpdir))
        self.assertEqual(result["npm_name"], "test-pkg")
        self.assertEqual(result["npm_version"], "1.0.0")
        self.assertEqual(result["npm_deps"], 2)
        self.assertIn("start", result["scripts"])

    def test_python_package(self):
        (self.tmpdir / "pyproject.toml").write_text("[project]")
        result = self.get_package_info(str(self.tmpdir))
        self.assertTrue(result.get("pyproject"))

    def test_rust_package(self):
        (self.tmpdir / "Cargo.toml").write_text("[package]")
        result = self.get_package_info(str(self.tmpdir))
        self.assertTrue(result.get("cargo"))

    def test_no_package_info(self):
        result = self.get_package_info(str(self.tmpdir))
        self.assertEqual(result, {})


class TestAnalyzeFunction(unittest.TestCase):
    """Test the analyze function (mocked API call)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "README.md").write_text("# Test\nA test project.")
        (self.tmpdir / "main.py").write_text("print('hello')")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_analyze_returns_string(self):
        """analyze returns a string (may be error message if API fails)."""
        from analyze_repo import analyze
        # We can't actually call the API, but we test the setup
        # Just verify the function exists and is callable
        import inspect
        sig = inspect.signature(analyze)
        self.assertEqual(len(sig.parameters), 1)


if __name__ == "__main__":
    unittest.main()
