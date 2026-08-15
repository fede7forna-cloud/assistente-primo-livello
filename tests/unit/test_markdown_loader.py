"""The loader enforces the citation contract, and refuses everything that would break it.

``doc_id`` and ``anchor`` are the two halves of the reference this assistant shows
to users and promises to keep valid. A file that cannot produce that reference
unambiguously is rejected at ingestion, loudly, rather than indexed into something
that cites badly later.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from assistant.ingestion.markdown_loader import MarkdownDocumentLoader, MarkdownFormatError

FRONT_MATTER = '---\ndoc_id: prova\ntitle: Prova\nversion: "1.0"\n---\n\n# Prova\n\n'


def _write(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def _load_one(directory: Path):
    return list(MarkdownDocumentLoader(directory).load())[0]


def test_loads_the_sample_corpus(sample_docs: Path) -> None:
    documents = list(MarkdownDocumentLoader(sample_docs).load())

    assert [document.doc_id for document in documents] == ["guida-esempio", "procedure-esempio"]
    assert documents[0].title == "Guida di esempio"
    assert documents[1].version == "2.1"
    assert [section.anchor for section in documents[0].sections] == [
        "primo-accesso",
        "creare-scheda",
        "stati-scheda",
    ]


def test_text_before_the_first_section_is_dropped(sample_docs: Path) -> None:
    """It carries no anchor, so it could not be cited — and RF-2 requires every
    indexed chunk to be citable."""
    document = list(MarkdownDocumentLoader(sample_docs).load())[0]

    assert "Documentazione fittizia" not in "".join(
        section.body for section in document.sections
    )


def test_subsections_stay_inside_their_parent_section(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "prova.md",
        FRONT_MATTER + "## Titolo {#titolo}\n\nCorpo.\n\n### Sotto\n\nDettaglio.\n",
    )

    document = _load_one(tmp_path)

    assert len(document.sections) == 1
    assert "### Sotto" in document.sections[0].body


def test_headings_inside_code_fences_are_not_sections(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "prova.md",
        FRONT_MATTER + "## Titolo {#titolo}\n\n```bash\n## non è un titolo\n```\n",
    )

    assert len(_load_one(tmp_path).sections) == 1


def test_missing_anchor_is_an_error_not_a_generated_slug(tmp_path: Path) -> None:
    """A slug derived from the title would change the day someone fixes a typo in
    that title, invalidating references already handed to users — silently."""
    _write(tmp_path, "prova.md", FRONT_MATTER + "## Titolo senza ancora\n\nCorpo.\n")

    with pytest.raises(MarkdownFormatError, match="senza ancora"):
        _load_one(tmp_path)


@pytest.mark.parametrize(
    ("label", "anchor"),
    [("maiuscole", "Titolo"), ("accenti", "però"), ("spazi", "due parole"), ("vuota", "")],
)
def test_malformed_anchors_are_rejected(tmp_path: Path, label: str, anchor: str) -> None:
    _write(tmp_path, "prova.md", FRONT_MATTER + f"## Titolo {{#{anchor}}}\n\nCorpo.\n")

    with pytest.raises(MarkdownFormatError):
        _load_one(tmp_path)


def test_duplicate_anchors_are_rejected(tmp_path: Path) -> None:
    """Two sections sharing an anchor make ``doc_id#anchor`` ambiguous."""
    _write(
        tmp_path,
        "prova.md",
        FRONT_MATTER + "## Uno {#stessa}\n\nCorpo.\n\n## Due {#stessa}\n\nCorpo.\n",
    )

    with pytest.raises(MarkdownFormatError, match="già usata"):
        _load_one(tmp_path)


def test_doc_id_must_match_the_filename(tmp_path: Path) -> None:
    """The reference shown to the user must lead back to a file."""
    _write(tmp_path, "altro-nome.md", FRONT_MATTER + "## Titolo {#titolo}\n\nCorpo.\n")

    with pytest.raises(MarkdownFormatError, match="diverso dal nome del file"):
        _load_one(tmp_path)


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("front-matter assente", "# Prova\n\n## Titolo {#titolo}\n\nCorpo.\n"),
        ("campo mancante", '---\ndoc_id: prova\ntitle: Prova\n---\n\n## T {#t}\n\nCorpo.\n'),
        ("nessuna sezione", FRONT_MATTER + "Solo testo, nessun titolo di secondo livello.\n"),
        ("sezione vuota", FRONT_MATTER + "## Titolo {#titolo}\n\n"),
    ],
)
def test_malformed_documents_are_rejected(tmp_path: Path, label: str, body: str) -> None:
    _write(tmp_path, "prova.md", body)

    with pytest.raises(MarkdownFormatError):
        _load_one(tmp_path)


def test_readme_is_not_indexed(tmp_path: Path) -> None:
    """It documents the format; indexing it would make it citable as product docs."""
    _write(tmp_path, "prova.md", FRONT_MATTER + "## Titolo {#titolo}\n\nCorpo.\n")
    _write(tmp_path, "README.md", "# Come si scrivono i documenti\n")

    documents = list(MarkdownDocumentLoader(tmp_path).load())

    assert [document.doc_id for document in documents] == ["prova"]


def test_missing_directory_is_reported(tmp_path: Path) -> None:
    with pytest.raises(MarkdownFormatError, match="non trovata"):
        list(MarkdownDocumentLoader(tmp_path / "assente").load())


def test_empty_directory_is_reported(tmp_path: Path) -> None:
    """An empty index does not fail anywhere later: it just escalates everything,
    which looks like a badly calibrated threshold rather than a missing corpus."""
    with pytest.raises(MarkdownFormatError, match="Nessun documento"):
        list(MarkdownDocumentLoader(tmp_path).load())
