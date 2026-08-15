"""Indexing end to end, on the test corpus, with fake adapters. No network."""

from __future__ import annotations

import pytest

from assistant.ingestion.chunker import SectionChunker
from assistant.ingestion.markdown_loader import MarkdownDocumentLoader
from assistant.ingestion.pipeline import IngestionError, IngestionPipeline
from tests.conftest import FakeEmbedder, InMemoryVectorStore


def _pipeline(docs_dir, embedder=None, store=None) -> IngestionPipeline:
    return IngestionPipeline(
        loader=MarkdownDocumentLoader(docs_dir),
        chunker=SectionChunker(max_chars=2000, overlap_chars=200),
        embedder=embedder or FakeEmbedder(),
        store=store or InMemoryVectorStore(),
    )


def test_the_sample_corpus_is_indexed(sample_docs, store, embedder) -> None:
    report = _pipeline(sample_docs, embedder, store).run()

    assert report.documents == 2
    assert report.sections == 5
    assert report.chunks == 5
    assert store.count() == 5
    assert embedder.documents_embedded == 5


def test_reindexing_is_idempotent(sample_docs, store) -> None:
    """The property that makes ``chunk_id`` worth deriving the way it is.

    Two runs over unchanged documentation must produce the same identifiers, or
    the second run would add duplicates that then compete in search results.
    """
    _pipeline(sample_docs, store=store).run()
    first = store.chunk_ids

    _pipeline(sample_docs, store=store).run()

    assert store.chunk_ids == first
    assert store.count() == len(first)


def test_chunk_ids_are_the_expected_references(sample_docs, store) -> None:
    _pipeline(sample_docs, store=store).run()

    assert set(store.chunk_ids) == {
        "guida-esempio#primo-accesso/0",
        "guida-esempio#creare-scheda/0",
        "guida-esempio#stati-scheda/0",
        "procedure-esempio#archiviare-scheda/0",
        "procedure-esempio#errori-comuni/0",
    }


def test_a_removed_section_disappears_from_the_index(sample_docs, tmp_path, store) -> None:
    """Clearing is not optional: a stale section would stay searchable, and a
    citation pointing at it could not be verified against anything."""
    for source in sample_docs.glob("*.md"):
        (tmp_path / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    _pipeline(tmp_path, store=store).run()
    assert "procedure-esempio#errori-comuni/0" in store.chunk_ids

    trimmed = (tmp_path / "procedure-esempio.md").read_text(encoding="utf-8")
    (tmp_path / "procedure-esempio.md").write_text(
        trimmed.split("## Messaggi di errore comuni")[0], encoding="utf-8"
    )
    _pipeline(tmp_path, store=store).run()

    assert "procedure-esempio#errori-comuni/0" not in store.chunk_ids


def test_a_broken_document_leaves_the_previous_index_intact(sample_docs, tmp_path, store) -> None:
    """Nothing is destroyed until everything has succeeded.

    A malformed heading in the last file must not wipe a working index and then
    fail halfway through rebuilding it.
    """
    for source in sample_docs.glob("*.md"):
        (tmp_path / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    _pipeline(tmp_path, store=store).run()
    before = store.chunk_ids

    (tmp_path / "rotto.md").write_text(
        '---\ndoc_id: rotto\ntitle: Rotto\nversion: "1.0"\n---\n\n## Titolo senza ancora\n\nCorpo.\n',
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        _pipeline(tmp_path, store=store).run()

    assert store.chunk_ids == before


def test_chunks_carry_everything_a_citation_needs(sample_docs, store) -> None:
    _pipeline(sample_docs, store=store).run()

    retrieved = store.search([1.0] + [0.0] * 63, limit=5)
    for item in retrieved:
        chunk = item.chunk
        assert chunk.doc_id and chunk.anchor and chunk.doc_title and chunk.section_title
        assert chunk.reference == f"{chunk.doc_id}#{chunk.anchor}"


def test_an_empty_corpus_is_refused(tmp_path, store) -> None:
    (tmp_path / "README.md").write_text("# Solo il readme\n", encoding="utf-8")

    with pytest.raises(Exception) as error:
        _pipeline(tmp_path, store=store).run()

    assert store.count() == 0
    assert error.type is not IngestionError or "indicizzabile" in str(error.value)
