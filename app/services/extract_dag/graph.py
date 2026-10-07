"""Extract DAG: leaves from documents, compute from other nodes, fetch after deps."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Leaf:
    """Value extracted from a page, document, or already-stored record."""

    id: str
    extractor: str
    goal: str
    kind: Literal["record", "document"] = "record"


@dataclass(frozen=True)
class Fetch:
    """I/O after dependencies are ready. Not a calculation. Not invented."""

    id: str
    deps: tuple[str, ...]
    fetcher: str
    goal: str


@dataclass(frozen=True)
class Compute:
    """Pure calculation from other nodes. A model writes this; another reviews it."""

    id: str
    deps: tuple[str, ...]
    goal: str
    output: str


@dataclass(frozen=True)
class ExtractGraph:
    id: str
    goal: str
    nodes: tuple[Leaf | Fetch | Compute, ...]

    def by_id(self) -> dict[str, Leaf | Fetch | Compute]:
        return {n.id: n for n in self.nodes}

    def compute_nodes(self) -> list[Compute]:
        return [n for n in self.nodes if isinstance(n, Compute)]


class GraphError(ValueError):
    pass


def topo_sort(graph: ExtractGraph) -> list[str]:
    """Kahn sort. Leaves have no deps; fetch/compute wait on named deps."""
    known = graph.by_id()
    if len(known) != len(graph.nodes):
        raise GraphError("duplicate node id")
    indeg: dict[str, int] = {n.id: 0 for n in graph.nodes}
    outgoing: dict[str, list[str]] = {n.id: [] for n in graph.nodes}
    for node in graph.nodes:
        deps = getattr(node, "deps", ())
        for dep in deps:
            if dep not in known:
                raise GraphError(f"{node.id} depends on missing {dep}")
            if isinstance(known[dep], Compute) is False and not isinstance(
                known[dep], (Leaf, Fetch, Compute)
            ):
                raise GraphError(f"{node.id} has bad dep {dep}")
            indeg[node.id] += 1
            outgoing[dep].append(node.id)
    ready = [nid for nid, d in indeg.items() if d == 0]
    ready.sort()
    ordered: list[str] = []
    while ready:
        nid = ready.pop(0)
        ordered.append(nid)
        for nxt in sorted(outgoing[nid]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
                ready.sort()
    if len(ordered) != len(graph.nodes):
        stuck = [nid for nid, d in indeg.items() if d]
        raise GraphError(f"cycle involving {stuck}")
    return ordered
