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
        return _goal_matches(node, source)


def _goal_matches(node: Compute, source: str) -> Review:
    """Second-pass: the function must do what the node goal says."""
    goal = (node.goal or "").lower()
    output = (node.output or "").lower()
    src = source.lower()
    person_out = "person dict" in output or output.strip() == "person"
    if person_out and any(
        p in goal for p in ("never invent", "do not invent", "nobody fits", "named nobody")
    ):
        if "none" not in src:
            return Review(False, "goal requires None when nobody is on the page or in Hunter")
    if "empty list is invalid" in goal:
        if "plan_for_job" not in src and "default" not in src and "operations" not in src:
            return Review(False, "goal requires operations defaults when titles are empty")
    if "from the posting" in goal:
        if "page_name" not in src:
            return Review(False, "goal is a posting value; function ignores page_name")
    if "prefer a posting" in goal or "posting-named" in goal:
        if "page_person" not in src:
            return Review(False, "goal prefers the posting person; function ignores page_person")
        if "leadership" in goal and "leadership_person" not in src:
            return Review(False, "goal uses leadership-page names; function ignores leadership_person")
        if "pick_candidate" not in src and "score_candidate" not in src:
            return Review(False, "goal is pick a title-matched person")
    elif "pick" in goal and "title" in goal:
        if "pick_candidate" not in src and "score_candidate" not in src:
            return Review(False, "goal is pick a title-matched person")
    return Review(True, "matches goal, deps, and stays offline")


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for child in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    return None
