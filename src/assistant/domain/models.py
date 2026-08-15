"""Core domain types for the first-level support assistant.

This module deliberately has no third-party imports. The domain layer describes
what the system *is* — documents, chunks, citations, answers — without knowing
how any of it is stored, embedded or generated. Anyone reviewing this codebase
should be able to read this file first and understand the product from it.

That constraint is also why validation here is plain ``__post_init__`` code
rather than Pydantic: Pydantic belongs at the system boundaries (configuration
loading, HTTP schemas, parsing of the model's structured output), not in the
core.

All types are frozen: transformations return new objects instead of mutating
existing ones, and collections are tuples so a value cannot be changed after it
has been handed to another layer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class Outcome(StrEnum):
    """How a request ended.

    Every request produces exactly one of these three outcomes. Making the
    outcome an enum rather than free text is what allows callers — the API, the
    CLI, the tests — to branch on the result without parsing prose.
    """

    ANSWER_FOUND = "answer_found"
    """The documentation covers the question: numbered steps plus citations."""

    NOT_IN_DOCUMENTATION = "not_in_documentation"
    """The documentation does not cover it. Hand over to a human operator."""

    AMBIGUOUS_QUESTION = "ambiguous_question"
    """The question needs clarifying before it can be answered or escalated."""


# --------------------------------------------------------------------------- #
# Documentation side: what the loader reads and what the retriever searches.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Section:
    """A titled, citable part of a document, as produced by a loader.

    ``anchor`` is the stable identifier of the section. It is the second half of
    the reference shown to the user (``doc_id#anchor``), so it must never be
    renamed or reused once published — see the conventions in CLAUDE.md.
    """

    title: str
    anchor: str
    body: str


@dataclass(frozen=True, slots=True)
class Document:
    """A source document, structured but not yet indexable.

    Loaders stop here. Turning sections into indexable units is the chunker's
    job, and keeping the two apart is what lets the chunking policy change
    (splitting long sections, merging short ones) without touching any loader.
    """

    doc_id: str
    title: str
    version: str
    sections: tuple[Section, ...]


@dataclass(frozen=True, slots=True)
class Chunk:
    """The unit that gets embedded, stored and retrieved.

    The document and section titles are copied in rather than referenced. A
    vector store hands back chunks in isolation, so a chunk has to carry
    everything needed to render a citation without a second lookup — the shape
    is dictated by how retrieval works, not by normalisation.

    ``ordinal`` is the position of the chunk within its document, used to keep
    ordering deterministic across runs and therefore reproducible in tests.
    """

    chunk_id: str
    doc_id: str
    doc_title: str
    section_title: str
    anchor: str
    text: str
    ordinal: int

    @property
    def reference(self) -> str:
        """The citable reference for this chunk, e.g. ``contratti-noleggio#cauzione``."""
        return f"{self.doc_id}#{self.anchor}"


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A chunk together with its relevance to one specific query.

    The score is not a property of the chunk — the same chunk scores differently
    against different questions — which is why it lives here and not on
    ``Chunk``, where it would be a meaningless field at ingestion time.

    ``score`` is a similarity in ``[0.0, 1.0]``, higher meaning more similar.
    See ``ports.VectorStore.search`` for why that direction matters.
    """

    chunk: Chunk
    score: float

    @property
    def reference(self) -> str:
        """The citable reference of the underlying chunk."""
        return self.chunk.reference


# --------------------------------------------------------------------------- #
# Answer side: what the model claims, and what we are willing to show.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CitationRef:
    """A source the model *claims* to have used. Unverified.

    This is what comes back from the language model: two identifiers and nothing
    else. It becomes a ``Citation`` only after the validator has matched it
    against the chunks actually retrieved for this question.
    """

    doc_id: str
    anchor: str

    @property
    def reference(self) -> str:
        """The claimed reference, in ``doc_id#anchor`` form."""
        return f"{self.doc_id}#{self.anchor}"


@dataclass(frozen=True, slots=True)
class Citation:
    """A verified source, resolved against a chunk that was really retrieved.

    It holds no text: a citation points at documentation, it does not reproduce
    it. Titles are carried so the reference can be rendered as a readable label
    without consulting the store again.
    """

    doc_id: str
    doc_title: str
    section_title: str
    anchor: str

    @property
    def reference(self) -> str:
        """The verified reference, in ``doc_id#anchor`` form."""
        return f"{self.doc_id}#{self.anchor}"

    @classmethod
    def from_chunk(cls, chunk: Chunk) -> Self:
        """Build a citation from a chunk that was actually retrieved."""
        return cls(
            doc_id=chunk.doc_id,
            doc_title=chunk.doc_title,
            section_title=chunk.section_title,
            anchor=chunk.anchor,
        )


@dataclass(frozen=True, slots=True)
class AnswerDraft:
    """Whatever the language model returned. Untrusted, deliberately unvalidated.

    There are no invariants here on purpose. A draft may claim an outcome its
    content does not support, or cite a section that was never retrieved — those
    are ordinary things for a model to do, and the point of this type is to make
    that possibility visible in every signature that handles it.

    A draft is never shown to a user. It becomes an ``Answer`` only by passing
    through the citation validator, and because the two types are distinct,
    skipping that step is a type error rather than a silent regression.
    """

    outcome: Outcome
    steps: tuple[str, ...] = ()
    citations: tuple[CitationRef, ...] = ()
    message: str = ""


@dataclass(frozen=True, slots=True)
class Answer:
    """A validated answer, safe to return to the user.

    The invariants enforced below make the functional requirements
    unrepresentable rather than merely checked: there is no way to construct an
    ``Answer`` that claims to have found something without numbered steps and at
    least one verified citation, and no way to escalate while smuggling in
    invented steps.

    Use the named constructors — ``found``, ``not_in_documentation``,
    ``ambiguous`` — rather than the raw initialiser, so the rules stay in one
    place.

    IMPORTANT — the ``ValueError`` below marks a defect in *our* code, never a
    path a user can trigger. A model answering ``ANSWER_FOUND`` while citing a
    section that was never retrieved is normal, expected traffic: the citation
    validator must catch it and downgrade the draft to
    ``NOT_IN_DOCUMENTATION`` *before* an ``Answer`` is constructed. If this
    exception ever surfaces at runtime, the bug is in the validator — do not
    "fix" it by relaxing these invariants, and do not let it propagate to the
    user in place of a proper escalation message.
    """

    outcome: Outcome
    steps: tuple[str, ...] = ()
    citations: tuple[Citation, ...] = ()
    message: str = ""

    def __post_init__(self) -> None:
        if self.outcome is Outcome.ANSWER_FOUND:
            if not self.steps:
                raise ValueError(
                    "Outcome.ANSWER_FOUND requires at least one step: an answer "
                    "without steps is not an answer."
                )
            if not self.citations:
                raise ValueError(
                    "Outcome.ANSWER_FOUND requires at least one verified citation. "
                    "An uncited answer must be downgraded to "
                    "Outcome.NOT_IN_DOCUMENTATION by the citation validator."
                )
            return

        if self.steps or self.citations:
            raise ValueError(
                f"{self.outcome} must carry neither steps nor citations: "
                "escalating while listing steps would present invented "
                "instructions as documented ones."
            )
        if not self.message.strip():
            raise ValueError(
                f"{self.outcome} requires a message telling the user what to do next."
            )

    @property
    def is_escalation(self) -> bool:
        """True when the request must be handed over to a human operator."""
        return self.outcome is Outcome.NOT_IN_DOCUMENTATION

    @classmethod
    def found(
        cls,
        steps: Sequence[str],
        citations: Sequence[Citation],
        message: str = "",
    ) -> Self:
        """An answer backed by the documentation.

        ``message`` is optional context around the steps; the steps and the
        citations are what must always be present.
        """
        return cls(
            outcome=Outcome.ANSWER_FOUND,
            steps=tuple(steps),
            citations=tuple(citations),
            message=message,
        )

    @classmethod
    def not_in_documentation(cls, message: str) -> Self:
        """The documentation does not cover the question; escalate to a human."""
        return cls(outcome=Outcome.NOT_IN_DOCUMENTATION, message=message)

    @classmethod
    def ambiguous(cls, message: str) -> Self:
        """The question needs clarifying before it can be answered or escalated."""
        return cls(outcome=Outcome.AMBIGUOUS_QUESTION, message=message)
