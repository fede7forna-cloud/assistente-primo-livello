"""Shared doubles and fixtures. No network, no model, no database.

Every port has a stand-in here, and the stand-ins honour the contracts written in
``domain/ports.py`` rather than merely satisfying the type checker. In particular
``InMemoryVectorStore`` returns a *similarity* in ``[0, 1]``, sorted descending —
the one thing an adapter can get backwards without anything crashing, so a fake
that got it wrong would hide exactly the bug the contract exists to prevent.

``FakeEmbedder`` is a real, tiny embedding model: bag of hashed words, L2
normalised. Lexical overlap therefore produces a high cosine and unrelated text a
low one, which is what lets the integration tests exercise the escalation
threshold instead of asserting against numbers pulled out of the air.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from pathlib import Path

import pytest

from assistant.domain.models import (
    AnswerDraft,
    Chunk,
    CitationRef,
    Outcome,
    RetrievedChunk,
)

_DIMENSIONS = 64
_WORD = re.compile(r"\w+", re.UNICODE)


# --------------------------------------------------------------------------- #
# Doubles
# --------------------------------------------------------------------------- #


class FakeEmbedder:
    """Deterministic bag-of-hashed-words embedder. Satisfies ``ports.Embedder``."""

    def __init__(self, query_prefix: str = "", passage_prefix: str = "") -> None:
        self.query_prefix = query_prefix
        self.passage_prefix = passage_prefix
        self.documents_embedded = 0
        self.queries_embedded = 0

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        self.documents_embedded += len(texts)
        return [_vector(f"{self.passage_prefix}{text}") for text in texts]

    def embed_query(self, text: str) -> Sequence[float]:
        self.queries_embedded += 1
        return _vector(f"{self.query_prefix}{text}")

    def warm_up(self) -> None:
        """Present so the API's start-up path can be exercised with this double."""


class InMemoryVectorStore:
    """Dict-backed vector store. Satisfies ``ports.VectorStore``."""

    def __init__(self) -> None:
        self._rows: dict[str, tuple[Chunk, Sequence[float]]] = {}
        self.upsert_calls = 0

    def upsert(
        self,
        chunks: Sequence[Chunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        self.upsert_calls += 1
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._rows[chunk.chunk_id] = (chunk, vector)

    def search(self, vector: Sequence[float], limit: int) -> Sequence[RetrievedChunk]:
        scored = [
            RetrievedChunk(chunk=chunk, score=_cosine(vector, stored))
            for chunk, stored in self._rows.values()
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return tuple(scored[:limit])

    def clear(self) -> None:
        self._rows.clear()

    def count(self) -> int:
        return len(self._rows)

    @property
    def chunk_ids(self) -> tuple[str, ...]:
        return tuple(self._rows)


class ScriptedVectorStore:
    """Returns preset scores, for tests about the threshold rather than similarity."""

    def __init__(self, scores: Sequence[float]) -> None:
        self._scores = tuple(scores)

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        raise NotImplementedError

    def search(self, vector: Sequence[float], limit: int) -> Sequence[RetrievedChunk]:
        rows = [
            RetrievedChunk(chunk=make_chunk(anchor=f"sezione-{index}", ordinal=index), score=score)
            for index, score in enumerate(self._scores)
        ]
        rows.sort(key=lambda item: item.score, reverse=True)
        return tuple(rows[:limit])

    def clear(self) -> None:
        raise NotImplementedError

    def count(self) -> int:
        return len(self._scores)


class FakeLLMClient:
    """Returns a scripted draft, or raises. Records what it was asked.

    ``contexts`` keeps the objects it received, not copies: that is what allows a
    test to assert the validator was handed *the same* context, by identity.
    """

    def __init__(self, draft: AnswerDraft | None = None, error: Exception | None = None) -> None:
        self._draft = draft
        self._error = error
        self.calls = 0
        self.questions: list[str] = []
        self.contexts: list[Sequence[RetrievedChunk]] = []

    def generate_answer(
        self,
        question: str,
        context: Sequence[RetrievedChunk],
    ) -> AnswerDraft:
        self.calls += 1
        self.questions.append(question)
        self.contexts.append(context)
        if self._error is not None:
            raise self._error
        assert self._draft is not None, "FakeLLMClient needs either a draft or an error"
        return self._draft


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #


def make_chunk(
    doc_id: str = "guida-esempio",
    anchor: str = "primo-accesso",
    text: str = "Testo della sezione.",
    doc_title: str = "Guida di esempio",
    section_title: str = "Primo accesso",
    ordinal: int = 0,
) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#{anchor}/0",
        doc_id=doc_id,
        doc_title=doc_title,
        section_title=section_title,
        anchor=anchor,
        text=text,
        ordinal=ordinal,
    )


def make_retrieved(score: float = 0.9, **kwargs: object) -> RetrievedChunk:
    return RetrievedChunk(chunk=make_chunk(**kwargs), score=score)  # type: ignore[arg-type]


def make_draft(
    outcome: Outcome = Outcome.ANSWER_FOUND,
    steps: Sequence[str] = ("Aprire la sezione **Schede**.",),
    citations: Sequence[tuple[str, str]] = (("guida-esempio", "primo-accesso"),),
    message: str = "",
) -> AnswerDraft:
    return AnswerDraft(
        outcome=outcome,
        steps=tuple(steps),
        citations=tuple(CitationRef(doc_id=doc, anchor=anchor) for doc, anchor in citations),
        message=message,
    )


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def sample_docs() -> Path:
    """The test corpus, deliberately unrelated to docs_source/."""
    return Path(__file__).parent / "fixtures" / "sample_docs"


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def make_llm():
    def _make(draft: AnswerDraft | None = None, error: Exception | None = None) -> FakeLLMClient:
        return FakeLLMClient(draft=draft, error=error)

    return _make


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #


def _vector(text: str) -> list[float]:
    counts = [0.0] * _DIMENSIONS
    for word in _WORD.findall(text.casefold()):
        counts[hash_word(word) % _DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in counts))
    return counts if norm == 0 else [value / norm for value in counts]


def hash_word(word: str) -> int:
    """Stable across processes, unlike ``hash()`` with PYTHONHASHSEED randomised."""
    value = 0
    for character in word:
        value = (value * 31 + ord(character)) % 1_000_003
    return value


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    return max(0.0, min(1.0, dot))
