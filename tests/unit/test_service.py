"""The orchestrator's three promises: gate 1 saves the call, gate 2 sees the same
context the model saw, and infrastructure faults never become an outcome."""

from __future__ import annotations

import pytest

from assistant.domain.models import Answer, Outcome
from assistant.retrieval.retriever import Retriever
from assistant.service import AssistantService
from tests.conftest import (
    FakeEmbedder,
    InMemoryVectorStore,
    ScriptedVectorStore,
    make_draft,
    make_retrieved,
)


class _StubRetriever:
    """Returns a fixed context, and counts how often it was consulted."""

    def __init__(self, context: tuple = (), error: Exception | None = None) -> None:
        self._context = context
        self._error = error
        self.calls = 0

    def retrieve(self, question: str) -> tuple:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._context


def _service(retriever, llm_client, store=None) -> AssistantService:
    return AssistantService(
        retriever=retriever,
        llm_client=llm_client,
        store=store or InMemoryVectorStore(),
    )


def test_closed_gate_1_never_calls_the_model(make_llm) -> None:
    """The whole point of gate 1: no tokens spent, nothing for the model to invent.

    Asserting the outcome alone would pass even if the model had been called and
    had happened to escalate on its own. The call count is the actual property.
    """
    llm = make_llm(draft=make_draft())
    retriever = _StubRetriever(context=())

    answer = _service(retriever, llm).ask("Come si configura il server DNS?")

    assert llm.calls == 0
    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION
    assert answer.is_escalation


def test_gate_1_uses_the_shared_escalation_message(make_llm) -> None:
    """Both gates land the user in the same situation and must say the same thing."""
    from assistant.generation.citation_validator import ESCALATION_MESSAGE

    answer = _service(_StubRetriever(context=()), make_llm(draft=make_draft())).ask("x")

    assert answer.message == ESCALATION_MESSAGE


def test_full_path_produces_a_validated_answer(make_llm) -> None:
    context = (make_retrieved(),)
    llm = make_llm(draft=make_draft(steps=("Aprire la sezione **Schede**.",)))

    answer = _service(_StubRetriever(context), llm).ask("Come creo una scheda?")

    assert answer.outcome is Outcome.ANSWER_FOUND
    assert answer.steps == ("Aprire la sezione **Schede**.",)
    assert answer.citations[0].reference == "guida-esempio#primo-accesso"


def test_validator_receives_the_same_context_object_as_the_model(make_llm) -> None:
    """Identity, not equality.

    If the context were rebuilt between the two stages, gate 2 would verify the
    citations against a different set than the model was shown, and the check
    would stop meaning anything while still passing.
    """
    context = (make_retrieved(),)
    llm = make_llm(draft=make_draft())

    _service(_StubRetriever(context), llm).ask("Come creo una scheda?")

    assert llm.contexts[0] is context


def test_invented_citation_is_degraded_by_the_service(make_llm) -> None:
    llm = make_llm(draft=make_draft(citations=(("manuale-fantasma", "sezione-x"),)))

    answer = _service(_StubRetriever((make_retrieved(),)), llm).ask("Come creo una scheda?")

    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION
    assert answer.steps == ()


class _Boom(RuntimeError):
    """Stands in for any adapter failure; the service must not know the difference."""


def test_model_failures_propagate_instead_of_becoming_an_outcome(make_llm) -> None:
    """``Outcome`` describes the documentation; an exception describes the system.

    Returning NOT_IN_DOCUMENTATION here would tell the user something false about
    the corpus, send them to open a ticket instead of retrying, and inflate the
    escalation rate with numbers no later analysis can separate out.
    """
    llm = make_llm(error=_Boom("Chiave API rifiutata."))

    with pytest.raises(_Boom):
        _service(_StubRetriever((make_retrieved(),)), llm).ask("Come creo una scheda?")


def test_retrieval_failures_propagate(make_llm) -> None:
    retriever = _StubRetriever(error=_Boom("Indice illeggibile."))

    with pytest.raises(_Boom):
        _service(retriever, make_llm(draft=make_draft())).ask("Come creo una scheda?")


def test_blank_question_is_rejected(make_llm) -> None:
    with pytest.raises(ValueError):
        _service(_StubRetriever((make_retrieved(),)), make_llm(draft=make_draft())).ask("   ")


def test_index_size_delegates_to_the_store(make_llm) -> None:
    store = InMemoryVectorStore()
    service = _service(_StubRetriever(()), make_llm(draft=make_draft()), store=store)

    assert service.index_size() == 0


def test_service_contains_no_exception_handling() -> None:
    """Structural: the rule above is only true while the module has nothing to catch."""
    from pathlib import Path
    import re

    import assistant.service as module

    source = Path(module.__file__).read_text(encoding="utf-8")

    assert not re.findall(r"^\s*(try:|except\b)", source, re.MULTILINE)


def test_threshold_is_enforced_through_the_real_retriever(make_llm) -> None:
    """End of the gate-1 path with the real Retriever rather than a stub."""
    llm = make_llm(draft=make_draft())
    retriever = Retriever(
        embedder=FakeEmbedder(),
        store=ScriptedVectorStore([0.79, 0.70]),
        top_k=5,
        similarity_threshold=0.80,
    )

    answer = _service(retriever, llm).ask("Domanda senza corrispondenze.")

    assert llm.calls == 0
    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION
    assert isinstance(answer, Answer)
