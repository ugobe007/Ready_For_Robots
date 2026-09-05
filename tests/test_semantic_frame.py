"""Tests for verb-anchor semantic frame extraction."""
from app.services.semantic_frame import parse_news_semantic_frame


AMAZON_HEADLINE = (
    "Amazon is planning to roll out automation at all of its logistics centers, "
    "reducing human labor by 50% while improving operational throughput by 75%."
)


def test_amazon_headline_actor_action_goals():
    frame = parse_news_semantic_frame(AMAZON_HEADLINE)
    assert frame.actor == "Amazon"
    assert frame.action_verb == "plan"
    assert frame.topic
    assert "automation" in frame.topic.lower()
    assert len(frame.goals) >= 2
    metrics = " ".join(g.metric.lower() for g in frame.goals)
    assert "human labor" in metrics or "labor" in metrics
    assert "throughput" in metrics
    quants = {g.quantifier for g in frame.goals if g.quantifier}
    assert "50%" in quants or "50" in quants
    assert "75%" in quants or "75" in quants
    assert frame.confidence >= 0.7
    assert "logistics_automation" in frame.ontology_concepts


def test_hyperbolic_headline_flags_promotional_language():
    frame = parse_news_semantic_frame(
        "Revolutionary startup unveils groundbreaking humanoid in historic CES debut"
    )
    assert frame.hyperbolic_terms
    assert any(t in frame.hyperbolic_terms for t in ("revolutionary", "groundbreaking", "historic"))


def test_descriptor_not_treated_as_actor():
    frame = parse_news_semantic_frame(
        "Major Chinese robotics firm Unitree launches new humanoid at CES"
    )
    assert frame.actor
    assert "major" not in frame.actor.lower()
    assert "unitree" in frame.actor.lower() or frame.actor == "Unitree"


def test_summary_line_includes_actor_and_goal():
    frame = parse_news_semantic_frame(AMAZON_HEADLINE)
    summary = frame.summary_line()
    assert "Amazon" in summary
    assert "goal" in summary.lower() or "50" in summary
