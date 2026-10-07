"""Second-model / AST review of compiled compute functions.

The live reviewer can be a model. Tests and default compile use this
deterministic checker: the function must match the node goal shape and
must not do I/O or invent mailboxes.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from app.services.extract_dag.graph import Compute

_FORBIDDEN_CALLS = frozenset(
    {
        "eval",
        "exec",
        "open",
        "__import__",
        "compile",
        "input",
        "breakpoint",
    }
)
_FORBIDDEN_MODULES = frozenset(
    {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "os",
        "sys",
        "pathlib",
        "hunter_client",
        "apollo_client",
        "daily_jobs_hunter",
    }
)
_FORBIDDEN_NAMES = frozenset(
    {
        "HunterClient",
        "ApolloProspectClient",
        "requests",
        "urlopen",
    }
)


@dataclass(frozen=True)
class Review:
    ok: bool
    reason: str = ""


class AstReviewer:
    """Stand-in for the reviewing model when paid LLM is off."""

    def review(self, node: Compute, source: str) -> Review:
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return Review(False, f"syntax error: {exc}")
        fn = _function_def(tree, f"compute_{node.id}")
        if fn is None:
            return Review(False, f"missing compute_{node.id}")
        args = [a.arg for a in fn.args.args]
        kwonly = [a.arg for a in fn.args.kwonlyargs]
        names = args + kwonly
        missing = [d for d in node.deps if d not in names]
        if missing:
            return Review(False, f"function does not take deps {missing}")
        for child in ast.walk(tree):
            if isinstance(child, ast.Import):
                for alias in child.names:
                    if alias.name.split(".")[0] in _FORBIDDEN_MODULES:
                        return Review(False, f"forbidden import {alias.name}")
            if isinstance(child, ast.ImportFrom):
                mod = child.module or ""
                parts = set(mod.split("."))
                if parts & _FORBIDDEN_MODULES:
                    return Review(False, f"forbidden import {mod}")
                if "apollo" in mod.lower():
                    return Review(False, f"forbidden import {mod}")
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in _FORBIDDEN_CALLS:
                    return Review(False, f"forbidden call {child.func.id}")
            if isinstance(child, ast.Name) and child.id in _FORBIDDEN_NAMES:
                return Review(False, f"forbidden name {child.id}")
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                if child.value.startswith("operations@") or "@company.com" in child.value:
                    return Review(False, "must not invent operations@ mailboxes")
        if "invent" in source.lower() and "never" not in source.lower():
            return Review(False, "function comments suggest invention")
        return Review(True, "matches deps and stays offline")


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for child in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    return None
