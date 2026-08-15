"""Sections to chunks: the whole chunking policy lives here and nowhere else.

Loaders stop at ``Document``; this module decides what actually gets embedded.
Keeping the two apart is what lets the policy below change — splitting long
sections, adjusting overlap — without touching a single loader.

The policy, in order:

* one section, one chunk, verbatim, as long as it fits within ``max_chars``.
  Sections in this project are written self-contained, so this is the normal
  case and the one that produces the best citations;
* over the limit, split on blank-line block boundaries, never mid-line;
* a single block over the limit — a long error table — is split between its
  lines, repeating the table header in every part, because a table fragment
  without its header cannot be read by anyone, model included;
* overlap is carried as whole blocks or lines. A raw character slice would cut
  a table row in the middle of a cell.

``Chunk.text`` stays verbatim: no document or section header is injected into
it. Those already travel in the chunk's own fields, and rendering them is
``prompts.py``'s job — mixing presentation into the indexed text would make the
chunker something other than a pure function of the document.
"""

from __future__ import annotations

import logging
import re

from assistant.domain.models import Chunk, Document, Section

logger = logging.getLogger(__name__)

_BLANK_LINE = re.compile(r"\r?\n[ \t]*\r?\n")
_TABLE_SEPARATOR = re.compile(r"^[ \t]*\|?[\s:|-]*\|[\s:|-]*$")

_BLOCK_SEPARATOR = "\n\n"
_LINE_SEPARATOR = "\n"


class SectionChunker:
    """Turns a document's sections into the units that get embedded and stored."""

    def __init__(self, max_chars: int, overlap_chars: int) -> None:
        if max_chars <= 0:
            raise ValueError(f"max_chars must be positive, got {max_chars}")
        if not 0 <= overlap_chars < max_chars:
            raise ValueError(
                f"overlap_chars ({overlap_chars}) must be in [0, max_chars) "
                f"with max_chars={max_chars}, otherwise splitting cannot terminate"
            )
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    def chunk_document(self, document: Document) -> tuple[Chunk, ...]:
        """Produce every chunk of one document, in reading order.

        ``chunk_id`` is derived only from ``doc_id``, the section anchor and the
        position within the section — never from the text, never from a global
        counter. Two ingestions of unchanged documentation therefore produce the
        same identifiers, which is what makes ``VectorStore.upsert`` idempotent
        instead of accumulating duplicates that compete in search results.

        The part index is always present, even for a section that fits in one
        chunk: a section that later grows past the limit then upserts ``/0`` and
        merely adds ``/1``, rather than orphaning an id that no longer exists.

        Note the residual case that identifiers alone cannot solve: a section
        that *shrinks* from three parts to two leaves the third behind, because
        upsert overwrites but never deletes. Replacing the documentation calls
        for ``VectorStore.clear()`` — see the procedure in CLAUDE.md.
        """
        chunks: list[Chunk] = []
        for section in document.sections:
            for part_index, text in enumerate(self._split(section)):
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.doc_id}#{section.anchor}/{part_index}",
                        doc_id=document.doc_id,
                        doc_title=document.title,
                        section_title=section.title,
                        anchor=section.anchor,
                        text=text,
                        ordinal=len(chunks),
                    )
                )
        return tuple(chunks)

    def _split(self, section: Section) -> tuple[str, ...]:
        if len(section.body) <= self._max_chars:
            return (section.body,)

        logger.debug(
            "Sezione '%s' (%d caratteri) suddivisa: limite %d",
            section.anchor,
            len(section.body),
            self._max_chars,
        )
        return self._pack(self._to_units(section))

    def _to_units(self, section: Section) -> tuple[str, ...]:
        """Break a section into the smallest pieces a split is allowed to fall on."""
        units: list[str] = []
        for block in _BLANK_LINE.split(section.body):
            block = block.strip("\n")
            if not block.strip():
                continue
            if len(block) <= self._max_chars:
                units.append(block)
            else:
                units.extend(self._split_block(block, section))
        return tuple(units)

    def _split_block(self, block: str, section: Section) -> list[str]:
        """Split one oversized block between its lines, never inside one.

        When the block is a Markdown table, its header and separator rows are
        repeated at the top of every part. Without them the second part of a
        permissions matrix is a grid of bare values.
        """
        lines = block.split(_LINE_SEPARATOR)
        header = _table_header(lines)
        parts: list[str] = []
        current = list(header)

        for line in lines[len(header) :]:
            if len(line) > self._max_chars:
                logger.warning(
                    "Sezione '%s': riga di %d caratteri oltre il limite di %d, "
                    "mantenuta intera per non spezzarla a metà",
                    section.anchor,
                    len(line),
                    self._max_chars,
                )
            too_long = _joined_length(current + [line], 1) > self._max_chars
            if current != header and too_long:
                parts.append(_LINE_SEPARATOR.join(current))
                current = list(header)
            current.append(line)

        if current != header:
            parts.append(_LINE_SEPARATOR.join(current))
        return parts

    def _pack(self, units: tuple[str, ...]) -> tuple[str, ...]:
        """Greedily fill parts up to ``max_chars``, carrying overlap between them."""
        parts: list[str] = []
        current: list[str] = []

        for unit in units:
            if current and _joined_length(current + [unit], 2) > self._max_chars:
                parts.append(_BLOCK_SEPARATOR.join(current))
                current = self._overlap(current)
            current.append(unit)

        if current:
            parts.append(_BLOCK_SEPARATOR.join(current))
        return tuple(parts)

    def _overlap(self, emitted: list[str]) -> list[str]:
        """The trailing whole units of a part, up to the overlap budget."""
        if self._overlap_chars <= 0:
            return []

        tail: list[str] = []
        for unit in reversed(emitted):
            if _joined_length([unit, *tail], 2) > self._overlap_chars:
                break
            tail.insert(0, unit)
        return tail


def _table_header(lines: list[str]) -> list[str]:
    """The header and separator rows of a Markdown table, or nothing."""
    if len(lines) < 2 or not lines[0].lstrip().startswith("|"):
        return []
    if not _TABLE_SEPARATOR.match(lines[1]):
        return []
    return lines[:2]


def _joined_length(units: list[str], separator_length: int) -> int:
    if not units:
        return 0
    return sum(len(unit) for unit in units) + separator_length * (len(units) - 1)
