"""Extract DAG: Model interprets. Code computes.

Decompose a request into leaves (page/document values), fetches (I/O after
deps), and compute nodes (deterministic functions). Topologically sort.
A writer emits each compute function; a reviewer checks it against the goal.
The graph compiles to one executable script.
"""
from app.services.extract_dag.compile import CompiledScript, compile_graph
from app.services.extract_dag.graph import Compute, ExtractGraph, Fetch, Leaf, topo_sort
from app.services.extract_dag.review import AstReviewer, Review

__all__ = [
    "AstReviewer",
    "CompiledScript",
    "Compute",
    "ExtractGraph",
    "Fetch",
    "Leaf",
    "Review",
    "compile_graph",
    "topo_sort",
]
