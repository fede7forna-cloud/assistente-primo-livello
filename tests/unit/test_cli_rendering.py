"""The customer's requirement, where it is actually satisfied.

"Numbered steps and clickable links to the section" is not met by the model, which
returns steps unnumbered and citations as ``doc_id`` plus ``anchor`` — deliberately,
because numbering and linking are presentation. The CLI is one of the two places
that owe the requirement, so this is where it gets a test.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pytest
from rich.console import Console

from assistant.cli import _BANNERS, _numbered, _source_line
from assistant.domain.models import Citation, Outcome

CITATION = Citation(
    doc_id="guida-esempio",
    doc_title="Guida di esempio",
    section_title="Primo accesso ad Archivio Alfa",
    anchor="primo-accesso",
)


def _render(renderable, **console_kwargs: object) -> str:
    buffer = io.StringIO()
    Console(file=buffer, width=100, **console_kwargs).print(renderable)  # type: ignore[arg-type]
    return buffer.getvalue()


def test_steps_are_numbered_in_output() -> None:
    output = _render(_numbered(("Aprire il browser.", "Inserire la password.", "Fare clic su Entra.")))

    assert re.search(r"\b1\b.+Aprire il browser", output)
    assert re.search(r"\b2\b.+Inserire la password", output)
    assert re.search(r"\b3\b.+Fare clic su Entra", output)


def test_inline_markdown_is_rendered_not_stripped() -> None:
    """Bold is how the documentation distinguishes a control from prose. Showing raw
    asterisks would lose that; removing them would lose it too."""
    output = _render(_numbered(("Fare clic su **Entra**.",)), force_terminal=True, legacy_windows=False)

    assert "\x1b[1m" in output, "il grassetto non è stato reso"
    assert "**" not in output, "gli asterischi sono rimasti nel testo"
    assert "Entra" in output


def test_a_step_containing_a_newline_cannot_renumber_the_list() -> None:
    output = _render(_numbered(("Prima riga\ne una seconda riga.", "Secondo passaggio.")))

    assert re.search(r"\b2\b.+Secondo passaggio", output)
    assert not re.search(r"\b3\b", output)


def test_a_citation_links_to_the_local_document(tmp_path: Path) -> None:
    """The loader guarantees the document lives at ``docs_dir/<doc_id>.md``. That
    invariant, imposed for citability, is what makes a real link possible here."""
    (tmp_path / "guida-esempio.md").write_text("# Guida\n", encoding="utf-8")

    output = _render(
        _source_line(CITATION, tmp_path), force_terminal=True, legacy_windows=False
    )

    links = re.findall(r"\x1b\]8;[^;]*;([^\x1b]+)\x1b", output)
    assert links, "nessun collegamento OSC 8 emesso"
    assert links[0].startswith("file:///")
    assert links[0].endswith("guida-esempio.md#primo-accesso")


def test_the_citation_shows_the_section_title_and_the_reference(tmp_path: Path) -> None:
    (tmp_path / "guida-esempio.md").write_text("# Guida\n", encoding="utf-8")

    output = _render(_source_line(CITATION, tmp_path))

    assert "Primo accesso ad Archivio Alfa" in output
    assert "guida-esempio#primo-accesso" in output


def test_a_missing_document_degrades_to_plain_text(tmp_path: Path) -> None:
    """A loader reading from somewhere other than a filesystem produces no link,
    and the reference is still printed."""
    output = _render(_source_line(CITATION, tmp_path), force_terminal=True, legacy_windows=False)

    assert not re.findall(r"\x1b\]8;[^;]*;[^\x1b]+\x1b", output)
    assert "guida-esempio#primo-accesso" in output


@pytest.mark.parametrize("outcome", list(Outcome))
def test_every_outcome_has_a_visible_indicator(outcome: Outcome) -> None:
    """Colour alone disappears into a pipe, a log file and a redirect — and with it
    the difference between an escalation and a request for clarification."""
    symbol, label, _style = _BANNERS[outcome]

    assert symbol.strip()
    assert label.strip()
    assert symbol.isascii(), "un simbolo non ASCII può non essere codificabile su console Windows"


def test_the_three_indicators_are_distinguishable() -> None:
    labels = {label for _symbol, label, _style in _BANNERS.values()}
    symbols = {symbol for symbol, _label, _style in _BANNERS.values()}

    assert len(labels) == len(_BANNERS)
    assert len(symbols) == len(_BANNERS)
