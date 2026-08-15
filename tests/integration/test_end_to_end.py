"""The whole path on real components, with only the model and the store faked.

Loader, chunker, retriever, both gates and the service are the production classes
here. What is replaced is the network: the embedder is a tiny deterministic model
and the vector store is a dictionary, both honouring the contracts in
``domain/ports.py``.
"""

from __future__ import annotations

import pytest

from assistant.domain.models import Outcome
from assistant.ingestion.chunker import SectionChunker
from assistant.ingestion.markdown_loader import MarkdownDocumentLoader
from assistant.ingestion.pipeline import IngestionPipeline
from assistant.retrieval.retriever import Retriever
from assistant.service import AssistantService
from tests.conftest import FakeEmbedder, InMemoryVectorStore, make_draft

THRESHOLD = 0.30


@pytest.fixture
def indexed(sample_docs) -> tuple[FakeEmbedder, InMemoryVectorStore]:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    IngestionPipeline(
        loader=MarkdownDocumentLoader(sample_docs),
        chunker=SectionChunker(max_chars=2000, overlap_chars=200),
        embedder=embedder,
        store=store,
    ).run()
    return embedder, store


def _service(indexed, llm) -> AssistantService:
    embedder, store = indexed
    retriever = Retriever(
        embedder=embedder, store=store, top_k=3, similarity_threshold=THRESHOLD
    )
    return AssistantService(retriever=retriever, llm_client=llm, store=store)


def test_a_documented_question_reaches_the_model_with_the_right_section(indexed, make_llm) -> None:
    llm = make_llm(
        draft=make_draft(
            steps=("Fare clic su **Azioni** e scegliere **Archivia**.",),
            citations=(("procedure-esempio", "archiviare-scheda"),),
        )
    )

    answer = _service(indexed, llm).ask("Come archiviare una scheda archiviazione")

    assert llm.calls == 1
    assert "procedure-esempio#archiviare-scheda" in {
        item.reference for item in llm.contexts[0]
    }
    assert answer.outcome is Outcome.ANSWER_FOUND
    assert answer.citations[0].section_title == "Archiviare una scheda"


def test_an_unrelated_question_closes_gate_1_before_the_model(indexed, make_llm) -> None:
    llm = make_llm(draft=make_draft())

    answer = _service(indexed, llm).ask("ricetta carbonara guanciale pecorino uova")

    assert llm.calls == 0
    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION


def test_an_invented_citation_is_caught_after_the_model(indexed, make_llm) -> None:
    """Gate 1 opened, the model got relevant context, and invented a source anyway.
    This is the case gate 1 structurally cannot see."""
    llm = make_llm(
        draft=make_draft(
            steps=("Fare clic su **Azioni**.",),
            citations=(("procedure-esempio", "sezione-che-non-esiste"),),
        )
    )

    answer = _service(indexed, llm).ask("Come archiviare una scheda archiviazione")

    assert llm.calls == 1
    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION
    assert answer.steps == ()


def test_the_model_never_sees_more_than_top_k_sections(indexed, make_llm) -> None:
    llm = make_llm(draft=make_draft(citations=(("guida-esempio", "primo-accesso"),)))

    _service(indexed, llm).ask("scheda")

    if llm.calls:
        assert len(llm.contexts[0]) <= 3


def test_index_size_is_visible_through_the_service(indexed, make_llm) -> None:
    assert _service(indexed, make_llm(draft=make_draft())).index_size() == 5


def test_replacing_the_documentation_does_not_touch_the_code(tmp_path, make_llm) -> None:
    """The architectural promise: a different corpus, zero changes to src/.

    Only the loader's directory changes here — no import, no branch, no
    configuration beyond a path.
    """
    (tmp_path / "manuale-altro.md").write_text(
        '---\ndoc_id: manuale-altro\ntitle: Manuale altro\nversion: "1.0"\n---\n\n'
        "# Manuale altro\n\n## Sostituire la cartuccia {#sostituire-cartuccia}\n\n"
        "Aprire lo sportello e rimuovere la cartuccia esaurita.\n",
        encoding="utf-8",
    )
    embedder, store = FakeEmbedder(), InMemoryVectorStore()
    IngestionPipeline(
        loader=MarkdownDocumentLoader(tmp_path),
        chunker=SectionChunker(2000, 200),
        embedder=embedder,
        store=store,
    ).run()

    llm = make_llm(
        draft=make_draft(
            steps=("Aprire lo sportello.",),
            citations=(("manuale-altro", "sostituire-cartuccia"),),
        )
    )
    service = AssistantService(
        retriever=Retriever(embedder, store, top_k=3, similarity_threshold=THRESHOLD),
        llm_client=llm,
        store=store,
    )

    answer = service.ask("sostituire cartuccia sportello")

    assert answer.outcome is Outcome.ANSWER_FOUND
    assert answer.citations[0].reference == "manuale-altro#sostituire-cartuccia"
