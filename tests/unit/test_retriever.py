"""Gate 1: the threshold, and what passes through it."""

from __future__ import annotations

import pytest

from assistant.retrieval.retriever import Retriever
from tests.conftest import FakeEmbedder, ScriptedVectorStore


def _retriever(scores, top_k: int = 5, threshold: float = 0.80) -> Retriever:
    return Retriever(
        embedder=FakeEmbedder(),
        store=ScriptedVectorStore(scores),
        top_k=top_k,
        similarity_threshold=threshold,
    )


def test_gate_closes_when_nothing_reaches_the_threshold() -> None:
    assert _retriever([0.79, 0.75, 0.70]).retrieve("una domanda") == ()


def test_gate_closes_on_an_empty_index() -> None:
    assert _retriever([]).retrieve("una domanda") == ()


def test_below_threshold_chunks_are_dropped_even_when_the_gate_opens() -> None:
    """``top_k`` is an upper bound on context, not a quota to fill.

    Passing the tail of barely-related sections would widen what the model is
    free to cite without making the answer better.
    """
    retrieved = _retriever([0.91, 0.86, 0.79, 0.72]).retrieve("una domanda")

    assert [round(item.score, 2) for item in retrieved] == [0.91, 0.86]


def test_a_score_equal_to_the_threshold_passes() -> None:
    assert len(_retriever([0.80, 0.79]).retrieve("una domanda")) == 1


def test_top_k_limits_what_is_considered() -> None:
    assert len(_retriever([0.95, 0.93, 0.92, 0.91], top_k=2).retrieve("una domanda")) == 2


def test_the_gate_uses_the_best_score_even_if_results_arrive_unsorted() -> None:
    """The port guarantees ordering; the gate does not depend on an adapter honouring it."""
    retrieved = _retriever([0.70, 0.95, 0.60]).retrieve("una domanda")

    assert len(retrieved) == 1
    assert retrieved[0].score == pytest.approx(0.95)


@pytest.mark.parametrize(
    ("top_k", "threshold"),
    [(0, 0.8), (-1, 0.8), (5, 1.5), (5, -0.1)],
)
def test_invalid_configuration_is_rejected_at_construction(top_k: int, threshold: float) -> None:
    with pytest.raises(ValueError):
        _retriever([0.9], top_k=top_k, threshold=threshold)


def test_blank_question_is_rejected() -> None:
    with pytest.raises(ValueError):
        _retriever([0.9]).retrieve("   ")


def test_the_query_is_embedded_as_a_query_not_as_a_passage() -> None:
    """Asymmetric models encode the two sides differently; using the wrong one degrades
    retrieval silently, which is why the port has two methods."""
    embedder = FakeEmbedder()
    Retriever(embedder, ScriptedVectorStore([0.9]), top_k=5, similarity_threshold=0.8).retrieve(
        "una domanda"
    )

    assert embedder.queries_embedded == 1
    assert embedder.documents_embedded == 0
