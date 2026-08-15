"""Adapter: Markdown files on disk to domain ``Document`` objects.

This is one implementation of ``ports.DocumentLoader`` and the only place in the
project that knows what a Markdown file looks like. A different source format —
HTML, PDF, a wiki export — means a sibling module here, not a change anywhere
else.

The rules enforced below are not stylistic. ``doc_id`` and ``anchor`` together
form ``doc_id#anchor``, the reference this assistant shows to users and promises
to keep valid. A file that cannot produce that reference unambiguously is
rejected at ingestion time, loudly, rather than being indexed into something
that cites badly later.

Error messages are in Italian: whoever runs the ingestion reads them, exactly as
with ``ConfigError`` in ``config.py``.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple

import yaml

from assistant.domain.models import Document, Section

logger = logging.getLogger(__name__)

_FRONT_MATTER = re.compile(
    r"\A---[ \t]*\r?\n(?P<meta>.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
    re.DOTALL,
)

# Only level-two headings are sections. Deeper headings stay inside the body of
# the section that contains them: the citable unit is the ## one, and splitting
# on ### would create chunks with no anchor of their own.
_HEADING = re.compile(r"^##[ \t]+\S")
_ANCHORED_HEADING = re.compile(
    r"^##[ \t]+(?P<title>.+?)[ \t]*\{#(?P<anchor>[^}]*)\}[ \t]*$"
)
_FENCE = re.compile(r"^[ \t]*(?:```|~~~)")

# Lowercase kebab-case, no accents: the anchor ends up in a URL fragment.
_ANCHOR_FORMAT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_REQUIRED_METADATA = ("doc_id", "title", "version")

# Files that document the format rather than the product. Excluded by name so
# that docs_source/README.md never becomes an indexed, citable document.
_NON_CONTENT_STEMS = frozenset({"readme"})


class MarkdownFormatError(ValueError):
    """A source file breaks the contract described in ``docs_source/README.md``.

    Always carries the file and, where it makes sense, the line: the person
    reading this message has to go and fix that exact spot.
    """


class _Heading(NamedTuple):
    title: str
    anchor: str
    line: int


class MarkdownDocumentLoader:
    """Reads ``*.md`` files from a directory. Satisfies ``ports.DocumentLoader``.

    The directory is a constructor argument, not a parameter of ``load()``:
    ``DocumentLoader`` must stay implementable by a loader that reads from an
    API and has no path to be given.
    """

    def __init__(self, docs_dir: Path) -> None:
        self._docs_dir = docs_dir

    def load(self) -> Iterator[Document]:
        """Yield one ``Document`` per Markdown file, in stable filename order.

        Raises:
            MarkdownFormatError: if the directory is missing or empty, or as
                soon as any file breaks the format contract. Ingesting a corpus
                that is partly broken would silently drop sections users may
                already be citing.
        """
        for path in self._source_files():
            yield self._load_file(path)

    def _source_files(self) -> tuple[Path, ...]:
        if not self._docs_dir.is_dir():
            raise MarkdownFormatError(
                f"Cartella della documentazione non trovata: {self._docs_dir}\n"
                "Verificare il valore di paths.docs_source in config/settings.yaml."
            )

        files = tuple(
            path
            for path in sorted(self._docs_dir.glob("*.md"))
            if path.stem.lower() not in _NON_CONTENT_STEMS
        )
        if not files:
            raise MarkdownFormatError(
                f"Nessun documento da indicizzare in {self._docs_dir}\n"
                "La cartella non contiene file .md oltre al README. Senza documenti "
                "l'assistente rimanderebbe ogni domanda all'assistenza umana."
            )
        return files

    def _load_file(self, path: Path) -> Document:
        text = _read_text(path)
        metadata, body, body_line = _split_front_matter(text, path)
        doc_id, title, version = _validated_metadata(metadata, path)
        return Document(
            doc_id=doc_id,
            title=title,
            version=version,
            sections=_parse_sections(body, path, body_line),
        )


def _read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MarkdownFormatError(f"Impossibile leggere {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise MarkdownFormatError(
            f"{path} non è codificato in UTF-8: {exc.reason}\n"
            "Salvare il file in UTF-8 e ripetere l'indicizzazione."
        ) from exc
    # A BOM would otherwise sit in front of the front-matter delimiter and make
    # the file look like it has none. Common enough on Windows to be worth it.
    return text.lstrip("﻿")


def _split_front_matter(text: str, path: Path) -> tuple[dict[str, Any], str, int]:
    """Return the parsed metadata, the remaining body, and the body's first line.

    The line number is carried through so that errors reported while parsing
    sections point at the real line in the file, not at an offset into the body.
    """
    match = _FRONT_MATTER.match(text)
    if match is None:
        raise MarkdownFormatError(
            f"{path}: front-matter YAML mancante.\n"
            "Il file deve iniziare con un blocco delimitato da --- contenente "
            f"{', '.join(_REQUIRED_METADATA)}."
        )

    try:
        metadata = yaml.safe_load(match.group("meta"))
    except yaml.YAMLError as exc:
        raise MarkdownFormatError(
            f"{path}: front-matter YAML non valido.\n{exc}"
        ) from exc

    if not isinstance(metadata, dict):
        raise MarkdownFormatError(
            f"{path}: il front-matter non è una mappa chiave/valore."
        )

    consumed = text[: match.end()]
    return metadata, text[match.end() :], consumed.count("\n") + 1


def _validated_metadata(metadata: dict[str, Any], path: Path) -> tuple[str, str, str]:
    values: list[str] = []
    for key in _REQUIRED_METADATA:
        raw = metadata.get(key)
        if raw is None or isinstance(raw, (dict, list)) or not str(raw).strip():
            raise MarkdownFormatError(
                f"{path}: campo '{key}' mancante o vuoto nel front-matter."
            )
        values.append(str(raw).strip())

    doc_id, title, version = values
    if doc_id != path.stem:
        raise MarkdownFormatError(
            f"{path}: doc_id '{doc_id}' diverso dal nome del file '{path.stem}'.\n"
            "I due devono coincidere: il riferimento mostrato all'utente è "
            "doc_id#ancora e deve permettere di risalire al file."
        )
    return doc_id, title, version


def _parse_sections(body: str, path: Path, first_line: int) -> tuple[Section, ...]:
    """Split the body on level-two headings, one ``Section`` each.

    Anything before the first heading — the H1 and the document's introduction —
    is dropped: it carries no anchor, so it could not be cited, and RF-2 requires
    every indexed chunk to be citable.
    """
    sections: list[Section] = []
    anchors: dict[str, int] = {}
    heading: _Heading | None = None
    buffer: list[str] = []
    in_fence = False

    for offset, line in enumerate(body.splitlines()):
        line_number = first_line + offset
        if _FENCE.match(line):
            in_fence = not in_fence
        if in_fence or not _HEADING.match(line):
            buffer.append(line)
            continue

        if heading is None:
            _log_dropped_preamble(buffer, path)
        else:
            sections.append(_build_section(heading, buffer, path))
        heading = _parse_heading(line, line_number, path, anchors)
        buffer = []

    if heading is None:
        raise MarkdownFormatError(
            f"{path}: nessuna sezione trovata.\n"
            "Un documento deve contenere almeno un titolo di secondo livello "
            "nella forma '## Titolo {#ancora}'."
        )
    sections.append(_build_section(heading, buffer, path))
    return tuple(sections)


def _parse_heading(
    line: str,
    line_number: int,
    path: Path,
    anchors: dict[str, int],
) -> _Heading:
    """Read one heading, refusing anything that cannot yield a stable anchor.

    A missing anchor is an error rather than something to derive from the title.
    A generated slug would silently change the day someone fixes a typo in the
    title, invalidating references already handed to users — the one failure the
    citation contract exists to prevent.
    """
    match = _ANCHORED_HEADING.match(line)
    if match is None:
        raise MarkdownFormatError(
            f"{path}:{line_number}: titolo di sezione senza ancora.\n"
            f"  {line.strip()}\n"
            "Attesa la forma '## Titolo {#ancora}'. L'ancora non viene dedotta dal "
            "titolo: è il riferimento pubblico della sezione e deve restare stabile "
            "anche se il titolo cambia."
        )

    anchor = match.group("anchor").strip()
    if not _ANCHOR_FORMAT.match(anchor):
        raise MarkdownFormatError(
            f"{path}:{line_number}: ancora '{anchor}' non valida.\n"
            "Sono ammessi solo minuscole, cifre e trattini singoli, senza accenti "
            "(es. {#verifica-danni}): l'ancora finisce in un indirizzo cliccabile."
        )

    if anchor in anchors:
        raise MarkdownFormatError(
            f"{path}:{line_number}: ancora '{anchor}' già usata alla riga "
            f"{anchors[anchor]}.\n"
            "Due sezioni con la stessa ancora rendono il riferimento "
            "doc_id#ancora ambiguo."
        )

    anchors[anchor] = line_number
    return _Heading(title=match.group("title").strip(), anchor=anchor, line=line_number)


def _build_section(heading: _Heading, buffer: list[str], path: Path) -> Section:
    body = "\n".join(buffer).strip()
    if not body:
        raise MarkdownFormatError(
            f"{path}:{heading.line}: la sezione '{heading.title}' è vuota.\n"
            "Una sezione senza testo verrebbe indicizzata come il solo titolo e "
            "citata senza avere nulla da dire."
        )
    return Section(title=heading.title, anchor=heading.anchor, body=body)


def _log_dropped_preamble(buffer: list[str], path: Path) -> None:
    preamble = "\n".join(buffer).strip()
    if preamble:
        logger.debug(
            "%s: %d caratteri prima della prima sezione ignorati (non citabili)",
            path.name,
            len(preamble),
        )
