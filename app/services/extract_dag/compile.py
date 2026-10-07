"""Compile an extract DAG into one executable script.

Writer model (or the reviewed library) emits a deterministic function per
compute node. Reviewer model (or AST reviewer) checks it against the goal.
Fetch/leaf nodes become lookups — they are not calculated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from app.services.extract_dag.graph import (
    Compute,
    ExtractGraph,
    Fetch,
    GraphError,
    Leaf,
    topo_sort,
)
from app.services.extract_dag.review import AstReviewer, Review


class FunctionWriter(Protocol):
    def write(self, node: Compute) -> str: ...

    def rewrite(self, node: Compute, source: str, reason: str) -> str: ...


class FunctionReviewer(Protocol):
    def review(self, node: Compute, source: str) -> Review: ...


class CompileError(RuntimeError):
    pass


@dataclass
class CompiledScript:
    graph_id: str
    source: str
    order: list[str]

    def run(
        self,
        leaves: dict[str, Any],
        fetchers: dict[str, Callable[..., Any]] | None = None,
    ) -> dict[str, Any]:
        ns: dict[str, Any] = {"__builtins__": __builtins__}
        exec(self.source, ns, ns)  # noqa: S102 — reviewed graph script
        runner = ns.get("run")
        if not callable(runner):
            raise CompileError("compiled script has no run()")
        return runner(leaves, fetchers or {})


class LibraryWriter:
    """Uses already-reviewed function bodies. No paid LLM."""

    def __init__(self, library: dict[str, str]):
        self.library = library

    def write(self, node: Compute) -> str:
        src = self.library.get(node.id)
        if not src:
            raise CompileError(f"no reviewed function for {node.id}")
        return src.strip() + "\n"

    def rewrite(self, node: Compute, source: str, reason: str) -> str:
        return self.write(node)


def compile_graph(
    graph: ExtractGraph,
    writer: FunctionWriter,
    reviewer: FunctionReviewer | None = None,
) -> CompiledScript:
    reviewer = reviewer or AstReviewer()
    order = topo_sort(graph)
    known = graph.by_id()
    functions: dict[str, str] = {}
    for nid in order:
        node = known[nid]
        if not isinstance(node, Compute):
            continue
        source = writer.write(node)
        verdict = reviewer.review(node, source)
        if not verdict.ok:
            source = writer.rewrite(node, source, verdict.reason)
            verdict = reviewer.review(node, source)
        if not verdict.ok:
            raise CompileError(f"{node.id} failed review: {verdict.reason}")
        functions[nid] = source
    script = emit_script(graph, order, functions)
    return CompiledScript(graph_id=graph.id, source=script, order=order)


def emit_script(
    graph: ExtractGraph,
    order: list[str],
    functions: dict[str, str],
) -> str:
    known = graph.by_id()
    parts = [
        f'"""Compiled extract DAG {graph.id}. Model interprets. Code computes."""\n',
        "from __future__ import annotations\n",
        "from typing import Any, Callable\n",
    ]
    for nid in order:
        if nid in functions:
            node = known[nid]
            if isinstance(node, Compute) and node.goal:
                parts.append(f"# goal: {node.goal}\n")
            parts.append(functions[nid].rstrip() + "\n")
    parts.append("\ndef run(leaves: dict[str, Any], fetchers: dict[str, Callable[..., Any]] | None = None) -> dict[str, Any]:\n")
    parts.append("    fetchers = fetchers or {}\n")
    parts.append("    values: dict[str, Any] = {}\n")
    for nid in order:
        node = known[nid]
        if isinstance(node, Leaf):
            parts.append(f"    values[{nid!r}] = leaves.get({nid!r})\n")
        elif isinstance(node, Fetch):
            kwargs = ", ".join(f"{d}=values[{d!r}]" for d in node.deps)
            parts.append(
                f"    values[{nid!r}] = fetchers[{nid!r}]({kwargs})\n"
            )
        elif isinstance(node, Compute):
            kwargs = ", ".join(f"{d}=values[{d!r}]" for d in node.deps)
            parts.append(
                f"    values[{nid!r}] = compute_{nid}({kwargs})\n"
            )
        else:
            raise GraphError(f"unknown node {nid}")
    parts.append("    return values\n")
    return "".join(parts)
