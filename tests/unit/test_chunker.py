"""Chunking policy, and the identifier that makes re-indexing idempotent."""

from __future__ import annotations

import pytest

from assistant.domain.models import Document, Section
from assistant.ingestion.chunker import SectionChunker


def _document(*sections: Section, doc_id: str = "guida-esempio") -> Document:
    return Document(
        doc_id=doc_id, title="Guida di esempio", version="1.0", sections=tuple(sections)
    )


def _section(anchor: str = "primo-accesso", body: str = "Corpo breve.") -> Section:
    return Section(title="Primo accesso", anchor=anchor, body=body)


def test_a_short_section_becomes_exactly_one_chunk() -> None:
    chunks = SectionChunker(2000, 200).chunk_document(_document(_section()))

    assert len(chunks) == 1
    assert chunks[0].text == "Corpo breve."


def test_chunk_id_is_stable_across_runs() -> None:
    """Derived only from doc_id, anchor and position — never from the text.

    A content hash would change on a fixed typo, leaving the old chunk orphaned in
    the store; an ordinal within the document would renumber everything after an
    inserted section.
    """
    document = _document(_section(), _section(anchor="creare-scheda"))
    chunker = SectionChunker(2000, 200)

    first = [chunk.chunk_id for chunk in chunker.chunk_document(document)]
    second = [chunk.chunk_id for chunk in chunker.chunk_document(document)]

    assert first == second == ["guida-esempio#primo-accesso/0", "guida-esempio#creare-scheda/0"]


def test_chunk_id_does_not_change_when_the_text_does() -> None:
    chunker = SectionChunker(2000, 200)

    before = chunker.chunk_document(_document(_section(body="Testo originale.")))
    after = chunker.chunk_document(_document(_section(body="Testo corretto.")))

    assert before[0].chunk_id == after[0].chunk_id


def test_inserting_a_section_does_not_renumber_the_others() -> None:
    chunker = SectionChunker(2000, 200)
    before = chunker.chunk_document(_document(_section(), _section(anchor="stati-scheda")))
    after = chunker.chunk_document(
        _document(_section(), _section(anchor="creare-scheda"), _section(anchor="stati-scheda"))
    )

    unchanged = {chunk.chunk_id for chunk in before}

    assert unchanged <= {chunk.chunk_id for chunk in after}


def test_the_part_index_is_always_present() -> None:
    """A section that later grows past the limit then upserts /0 and adds /1,
    instead of orphaning an id that no longer exists."""
    chunks = SectionChunker(2000, 200).chunk_document(_document(_section()))

    assert chunks[0].chunk_id.endswith("/0")


def test_ordinal_follows_reading_order() -> None:
    document = _document(_section(), _section(anchor="creare-scheda"), _section(anchor="stati-scheda"))

    chunks = SectionChunker(2000, 200).chunk_document(document)

    assert [chunk.ordinal for chunk in chunks] == [0, 1, 2]


def test_reference_is_the_citable_form() -> None:
    chunks = SectionChunker(2000, 200).chunk_document(_document(_section()))

    assert chunks[0].reference == "guida-esempio#primo-accesso"


def test_long_sections_split_on_block_boundaries() -> None:
    body = "\n\n".join(f"Paragrafo numero {index} con un po' di testo." * 3 for index in range(10))

    chunks = SectionChunker(300, 50).chunk_document(_document(_section(body=body)))

    assert len(chunks) > 1
    assert [chunk.chunk_id for chunk in chunks] == [
        f"guida-esempio#primo-accesso/{index}" for index in range(len(chunks))
    ]


def test_a_long_table_keeps_its_header_in_every_part() -> None:
    """Without the header, the second part of a table is a grid of bare values."""
    header = "| Codice | Messaggio | Azione |\n|---|---|---|"
    rows = "\n".join(f"| ALF-{100 + i} | Messaggio numero {i} | Riprovare |" for i in range(40))

    chunks = SectionChunker(600, 100).chunk_document(_document(_section(body=f"{header}\n{rows}")))

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.text.startswith("| Codice | Messaggio | Azione |")


def test_table_rows_are_never_cut_in_half() -> None:
    header = "| Codice | Messaggio | Azione |\n|---|---|---|"
    rows = "\n".join(f"| ALF-{100 + i} | Messaggio numero {i} | Riprovare |" for i in range(40))

    chunks = SectionChunker(600, 100).chunk_document(_document(_section(body=f"{header}\n{rows}")))

    for chunk in chunks:
        for line in chunk.text.splitlines():
            if line.startswith("| ALF-"):
                assert line.endswith("|"), f"riga troncata: {line!r}"


@pytest.mark.parametrize(("max_chars", "overlap"), [(0, 0), (-1, 0), (100, 100), (100, 150)])
def test_invalid_limits_are_rejected(max_chars: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        SectionChunker(max_chars, overlap)
