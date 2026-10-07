"""Extract DAG: topo sort, review, compile, run. Model interprets. Code computes."""
from app.services.extract_dag.compile import (
    CompileError,
    LibraryWriter,
    compile_graph,
)
from app.services.extract_dag.decision_maker import (
    DECISION_MAKER_GRAPH,
    compiled_decision_maker,
    run_decision_maker_dag,
)
from app.services.extract_dag.graph import Compute, ExtractGraph, GraphError, Leaf, topo_sort
from app.services.extract_dag.review import AstReviewer


def test_topo_sort_leaves_before_compute():
    graph = ExtractGraph(
        id="toy",
        goal="add",
        nodes=(
            Leaf("a", extractor="record.a", goal="a"),
            Leaf("b", extractor="record.b", goal="b"),
            Compute("sum", deps=("a", "b"), goal="a+b", output="int"),
        ),
    )
    assert topo_sort(graph) == ["a", "b", "sum"]


def test_topo_sort_detects_cycle():
    graph = ExtractGraph(
        id="cycle",
        goal="bad",
        nodes=(
            Compute("x", deps=("y",), goal="x", output="x"),
            Compute("y", deps=("x",), goal="y", output="y"),
        ),
    )
    try:
        topo_sort(graph)
    except GraphError as exc:
        assert "cycle" in str(exc)
    else:
        raise AssertionError("expected cycle")


def test_reviewer_rejects_network_and_invented_mail():
    node = Compute("decision_maker", deps=("hunter_people",), goal="pick", output="person")
    reviewer = AstReviewer()
    bad_net = """
def compute_decision_maker(*, hunter_people):
    import requests
    return requests.get("https://example.com").json()
"""
    assert reviewer.review(node, bad_net).ok is False
    bad_mail = """
def compute_decision_maker(*, hunter_people):
    return {"email": "operations@company.com", "name": "Ops"}
"""
    assert reviewer.review(node, bad_mail).ok is False


def test_reviewer_rejects_wrong_deps():
    node = Compute("sum", deps=("a", "b"), goal="a+b", output="int")
    src = "def compute_sum(*, a):\n    return a\n"
    assert AstReviewer().review(node, src).ok is False


def test_compile_and_run_toy_graph():
    graph = ExtractGraph(
        id="toy",
        goal="add",
        nodes=(
            Leaf("a", extractor="record.a", goal="a"),
            Leaf("b", extractor="record.b", goal="b"),
            Compute("sum", deps=("a", "b"), goal="add a and b as integers", output="int"),
        ),
    )
    library = {
        "sum": "def compute_sum(*, a, b):\n    return int(a or 0) + int(b or 0)\n"
    }
    compiled = compile_graph(graph, LibraryWriter(library), AstReviewer())
    assert "def compute_sum" in compiled.source
    assert compiled.run({"a": 2, "b": 3})["sum"] == 5


def test_compile_fails_when_review_fails():
    graph = ExtractGraph(
        id="bad",
        goal="net",
        nodes=(
            Leaf("a", extractor="record.a", goal="a"),
            Compute("out", deps=("a",), goal="fetch", output="x"),
        ),
    )
    library = {
        "out": "def compute_out(*, a):\n    import requests\n    return a\n"
    }
    try:
        compile_graph(graph, LibraryWriter(library), AstReviewer())
    except CompileError:
        return
    raise AssertionError("expected CompileError")


def test_decision_maker_dag_picks_title_not_cdo():
    compiled = compiled_decision_maker()
    assert compiled.order[0] in {"employer", "job_text", "action", "locality", "domain", "page_name", "page_title"}
    assert compiled.order[-1] == "decision_maker"
    assert "hunter_people" in compiled.order
    people = [
        {
            "email": "kelli@harrishealth.org",
            "name": "Kelli Fondren",
            "title": "Chief Development Officer",
            "confidence": 99,
        },
        {
            "email": "priya@harrishealth.org",
            "name": "Priya Shah",
            "title": "Pharmacy Operations Manager",
            "confidence": 80,
        },
    ]

    def fetch_people(**kwargs):
        assert kwargs["employer"] == "Harris Health"
        return people

    out = run_decision_maker_dag(
        {
            "company_name": "Harris Health",
            "action": "delivery",
            "robot_compatible_task": "Pharmacy cart loop",
            "observed_workflow": "Move filled carts from pharmacy to nursing units",
            "locality": "Houston, TX",
        },
        domain="harrishealth.org",
        fetchers={"hunter_people": fetch_people},
    )
    assert out["job_function"] == "pharmacy"
    assert "Director of Pharmacy" in out["target_titles"]
    assert out["decision_maker"]["email"] == "priya@harrishealth.org"


def test_decision_maker_dag_miss_is_none():
    out = run_decision_maker_dag(
        {
            "company_name": "GEODIS",
            "action": "pallet_move",
            "robot_compatible_task": "Trailer unloading",
            "locality": "Plainfield, IN",
        },
        domain="geodis.com",
        fetchers={
            "hunter_people": lambda **kwargs: [
                {
                    "email": "rob@geodis.com",
                    "name": "Rob",
                    "title": "Security Operations",
                    "confidence": 95,
                }
            ]
        },
    )
    assert out["decision_maker"] is None
