"""The HTTP contract: an escalation is a 200, a fault is a 503.

The application's start-up is deliberately bypassed. ``lifespan`` reads the real
configuration and downloads an embedding model, neither of which belongs in a
test suite; the state it would have produced is injected instead, which is the
same seam the API itself uses to reach its dependencies.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from assistant.api.app import app
from assistant.domain.models import Answer, Citation, Outcome
from assistant.generation.openrouter_client import LLMError
from assistant.retrieval.chroma_store import VectorStoreError
from assistant.retrieval.local_embedder import EmbeddingError

CITATION = Citation(
    doc_id="procedure-esempio",
    doc_title="Procedure di esempio",
    section_title="Archiviare una scheda",
    anchor="archiviare-scheda",
)
STEPS = ("Aprire la scheda.", "Fare clic su **Azioni** e scegliere **Archivia**.")


class _StubService:
    def __init__(self, answer: Answer | None = None, error: Exception | None = None, size=5) -> None:
        self._answer = answer
        self._error = error
        self._size = size

    def ask(self, question: str) -> Answer:
        if self._error is not None:
            raise self._error
        assert self._answer is not None
        return self._answer

    def index_size(self) -> int:
        if isinstance(self._size, Exception):
            raise self._size
        return self._size


@pytest.fixture
def make_client():
    """Inject application state without running ``lifespan``, and restore it after."""
    previous = getattr(app.state, "components", None)

    def _make(answer=None, error=None, size=5, url_template=None) -> TestClient:
        app.state.components = SimpleNamespace(
            settings=SimpleNamespace(
                documentation=SimpleNamespace(url_template=url_template),
                llm=SimpleNamespace(model="modello-llm"),
                embedding=SimpleNamespace(model="modello-embedding"),
            ),
            service=_StubService(answer, error, size),
            embedder=None,
            store=None,
        )
        return TestClient(app)

    yield _make
    app.state.components = previous


def test_an_answer_is_returned_with_its_steps_and_citations(make_client) -> None:
    client = make_client(answer=Answer.found(steps=STEPS, citations=(CITATION,)))

    response = client.post("/chat", json={"question": "Come archivio una scheda?"})

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "answer_found"
    assert body["steps"] == list(STEPS)
    assert body["citations"][0]["reference"] == "procedure-esempio#archiviare-scheda"
    assert body["citations"][0]["section_title"] == "Archiviare una scheda"


def test_steps_are_not_numbered_by_the_server(make_client) -> None:
    """The order of the array is the numbering. Baking "1. " into the strings would
    force every client to strip it back off."""
    client = make_client(answer=Answer.found(steps=STEPS, citations=(CITATION,)))

    steps = client.post("/chat", json={"question": "x"}).json()["steps"]

    assert not any(step.lstrip().startswith(("1.", "-", "*")) for step in steps)


def test_inline_markdown_survives(make_client) -> None:
    """It is the documentation's own emphasis, distinguishing a control from prose."""
    client = make_client(answer=Answer.found(steps=STEPS, citations=(CITATION,)))

    steps = client.post("/chat", json={"question": "x"}).json()["steps"]

    assert "**Azioni**" in steps[1]


@pytest.mark.parametrize(
    ("outcome", "answer"),
    [
        (Outcome.NOT_IN_DOCUMENTATION, Answer.not_in_documentation("Contatta l'assistenza.")),
        (Outcome.AMBIGUOUS_QUESTION, Answer.ambiguous("Quale scheda intendi?")),
    ],
)
def test_escalation_and_clarification_are_successful_responses(
    make_client, outcome: Outcome, answer: Answer
) -> None:
    """Not an error: a client that retried on 4xx/5xx would retry a question that
    can never succeed."""
    response = make_client(answer=answer).post("/chat", json={"question": "x"})

    assert response.status_code == 200
    assert response.json()["outcome"] == outcome.value
    assert response.json()["steps"] == []


@pytest.mark.parametrize(
    "error",
    [
        LLMError("Chiave API rifiutata da OpenRouter."),
        EmbeddingError("Impossibile caricare il modello di embedding."),
        VectorStoreError("L'indice usa la metrica 'l2'."),
    ],
)
def test_infrastructure_faults_become_503_with_the_original_message(make_client, error) -> None:
    """A fault is not a verdict on the documentation, and the adapter's message
    already says what to check."""
    response = make_client(error=error).post("/chat", json={"question": "x"})

    assert response.status_code == 503
    assert response.json()["detail"] == str(error)


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        ("domanda vuota", {"question": ""}),
        ("campo mancante", {}),
        ("campo estraneo", {"question": "x", "extra": 1}),
    ],
)
def test_malformed_requests_are_rejected(make_client, label: str, payload: dict) -> None:
    client = make_client(answer=Answer.not_in_documentation("x"))

    assert client.post("/chat", json=payload).status_code == 422, label


def test_health_reports_a_usable_deployment(make_client) -> None:
    response = make_client(size=5).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "indexed_chunks": 5,
        "model": "modello-llm",
        "embedding_model": "modello-embedding",
    }


def test_an_empty_index_is_not_healthy(make_client) -> None:
    """With nothing indexed the assistant escalates every question, whatever it is
    asked. A monitor has to see that."""
    response = make_client(size=0).get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_an_unreadable_index_is_reported_as_unavailable(make_client) -> None:
    response = make_client(size=VectorStoreError("Indice illeggibile.")).get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Indice illeggibile."


def test_citation_url_is_absent_without_a_template(make_client) -> None:
    """Never a file:// URL: it would be dead on the client and would expose the
    server's filesystem layout."""
    client = make_client(answer=Answer.found(steps=STEPS, citations=(CITATION,)))

    citation = client.post("/chat", json={"question": "x"}).json()["citations"][0]

    assert citation["url"] is None
    assert citation["doc_id"] and citation["anchor"]


def test_citation_url_is_built_from_the_template(make_client) -> None:
    client = make_client(
        answer=Answer.found(steps=STEPS, citations=(CITATION,)),
        url_template="https://docs.esempio.it/{doc_id}#{anchor}",
    )

    citation = client.post("/chat", json={"question": "x"}).json()["citations"][0]

    assert citation["url"] == "https://docs.esempio.it/procedure-esempio#archiviare-scheda"


def test_the_openapi_schema_declares_the_three_outcomes(make_client) -> None:
    """Clients branch on this field; the values belong in the schema, not in prose."""
    schema = make_client(answer=Answer.not_in_documentation("x")).get("/openapi.json").json()

    assert set(schema["components"]["schemas"]["Outcome"]["enum"]) == {
        "answer_found",
        "not_in_documentation",
        "ambiguous_question",
    }
