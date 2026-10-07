"""Extract DAG: topo sort, review, compile, run. Model interprets. Code computes."""
from app.services.extract_dag.compile import (
    CompileError,
    LibraryWriter,
    compile_graph,
)
from app.services.extract_dag.decision_maker import (
    DECISION_MAKER_GRAPH,
    compiled_decision_maker,
    extract_leaf,
    run_decision_maker_dag,
)
from app.services.extract_dag.graph import Compute, ExtractGraph, Fetch, GraphError, Leaf, topo_sort
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


def test_topo_sort_fetch_waits_on_compute():
    graph = ExtractGraph(
        id="fetch",
        goal="io after calc",
        nodes=(
            Leaf("q", extractor="record.q", goal="q"),
            Compute("dept", deps=("q",), goal="dept", output="str"),
            Fetch("people", deps=("dept",), fetcher="hunter", goal="people"),
            Compute("pick", deps=("people",), goal="pick", output="person"),
        ),
    )
    assert topo_sort(graph) == ["q", "dept", "people", "pick"]


def test_reviewer_rejects_function_that_ignores_goal():
    node = Compute(
        "decision_maker",
        deps=("hunter_people", "page_person"),
        goal="Prefer a posting-named person. Else pick a Hunter person whose title matches. None if nobody fits. Do not invent a name or mailbox.",
        output="person dict or None",
    )
    always_ops = """
def compute_decision_maker(*, hunter_people, page_person):
    return {"name": "Ops Lead", "email": "lead@readyforrobots.com"}
"""
    verdict = AstReviewer().review(node, always_ops)
    assert verdict.ok is False


def test_reviewer_accepts_library_decision_maker():
    from app.services.extract_dag.library_decision_maker import LIBRARY

    node = next(n for n in DECISION_MAKER_GRAPH.nodes if getattr(n, "id", None) == "decision_maker")
    assert AstReviewer().review(node, LIBRARY["decision_maker"]).ok is True
    page = next(n for n in DECISION_MAKER_GRAPH.nodes if getattr(n, "id", None) == "page_person")
    assert AstReviewer().review(page, LIBRARY["page_person"]).ok is True


def test_extract_leaf_reads_posting_name():
    node = next(n for n in DECISION_MAKER_GRAPH.nodes if n.id == "page_name")
    row = {
        "company_name": "Harris Health",
        "provenance": {"contact_name": "Maya Chen", "contact_title": "Pharmacy Operations Manager"},
    }
    assert extract_leaf(node, row) == "Maya Chen"


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


def test_decision_maker_dag_prefers_posting_name_when_title_matches():
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
            "confidence": 91,
        },
    ]
    out = run_decision_maker_dag(
        {
            "company_name": "Harris Health",
            "action": "delivery",
            "robot_compatible_task": "Pharmacy cart loop",
            "locality": "Houston, TX",
            "provenance": {
                "contact_name": "Maya Chen",
                "contact_title": "Pharmacy Operations Manager",
            },
        },
        domain="harrishealth.org",
        fetchers={"hunter_people": lambda **kwargs: people},
    )
    assert out["page_person"]["name"] == "Maya Chen"
    assert out["decision_maker"]["name"] == "Maya Chen"
    assert out["decision_maker"]["source"] == "page"


def test_decision_maker_dag_skips_posting_cdo_for_hunter_pharmacy():
    out = run_decision_maker_dag(
        {
            "company_name": "Harris Health",
            "action": "delivery",
            "robot_compatible_task": "Pharmacy cart loop",
            "locality": "Houston, TX",
            "provenance": {
                "contact_name": "Kelli Fondren",
                "contact_title": "Chief Development Officer",
            },
        },
        domain="harrishealth.org",
        fetchers={
            "hunter_people": lambda **kwargs: [
                {
                    "email": "priya@harrishealth.org",
                    "name": "Priya Shah",
                    "title": "Pharmacy Operations Manager",
                    "confidence": 91,
                }
            ]
        },
    )
    assert out["page_person"]["name"] == "Kelli Fondren"
    assert out["decision_maker"]["email"] == "priya@harrishealth.org"


def test_compiled_script_is_one_run_function():
    compiled = compiled_decision_maker()
    assert "def run(leaves" in compiled.source
    leaf_ids = [n.id for n in DECISION_MAKER_GRAPH.nodes if isinstance(n, Leaf)]
    last_leaf = max(compiled.order.index(i) for i in leaf_ids)
    first_fetch = compiled.order.index("hunter_people")
    assert last_leaf < first_fetch
    assert compiled.order.index("page_person") < compiled.order.index("decision_maker")
    assert compiled.order.index("departments") < compiled.order.index("hunter_people")
    assert compiled.order.index("hunter_people") < compiled.order.index("decision_maker")
    assert "# goal:" in compiled.source
