"""Ports: the interfaces the domain expects the outside world to satisfy.

Every dependency that touches the world — a file format, an embedding model, a
vector database, an LLM provider — sits behind one of these protocols. Swapping
Markdown for Confluence, ChromaDB for FAISS or OpenRouter for another provider
means writing a new adapter that satisfies the relevant protocol; nothing in the
domain, the service or the tests changes.

They are ``Protocol`` classes rather than base classes: adapters conform
structurally and never import the domain in order to inherit from it, which
keeps the dependency arrow pointing inwards. Fakes in the test suite conform the
same way, with no registration step.

All methods are synchronous. FastAPI runs synchronous handlers in a worker
thread, so nothing here needs to be awaited.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from assistant.domain.models import AnswerDraft, Chunk, Document, RetrievedChunk

Vector = Sequence[float]
"""A dense embedding.

Typed as a plain sequence of floats so the domain never depends on numpy. An
adapter is free to hand back a numpy array — it satisfies this alias — but no
code in the core may assume one.
"""


class DocumentLoader(Protocol):
    """Reads the documentation and returns it as structured documents.

    Implementations own one source format: Markdown files on disk today, HTML,
    PDF or an export from a wiki tomorrow.
    """

    def load(self) -> Iterable[Document]:
        """Yield every document available from this loader's source.

        The source — a directory, a URL, a set of credentials — is supplied to
        the adapter's constructor, not to this method. If it were a parameter
        here, the port would be assuming that documentation lives on a
        filesystem, and a loader that reads from a wiki API has no path to pass.

        Returns an iterable rather than a concrete sequence so a large corpus can
        be streamed instead of materialised in memory.
        """
        ...


class Embedder(Protocol):
    """Turns text into vectors.

    Two methods rather than one because several embedding families — e5, bge,
    gte — encode passages and queries differently, usually via distinct
    instruction prefixes. A single ``embed`` would either rule those models out
    or force every caller to know which side of the comparison it is on.
    """

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Vector]:
        """Embed chunk texts for indexing.

        Returns one vector per input, in the same order. All vectors returned by
        a given embedder must have the same dimension.
        """
        ...

    def embed_query(self, text: str) -> Vector:
        """Embed a user question for searching.

        The result must be comparable with vectors produced by
        ``embed_documents`` on the same embedder instance.
        """
        ...


class VectorStore(Protocol):
    """Persists chunks with their vectors and answers similarity searches."""

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        """Store chunks and their vectors, replacing any entry with the same id.

        ``chunks[i]`` corresponds to ``vectors[i]``; implementations may reject
        mismatched lengths. Upsert rather than append so that re-running the
        ingestion over unchanged documentation is idempotent instead of
        producing duplicate chunks that would then compete in search results.
        """
        ...

    def search(self, vector: Vector, limit: int) -> Sequence[RetrievedChunk]:
        """Return at most ``limit`` chunks, most similar first.

        ``RetrievedChunk.score`` must be a **similarity** in ``[0.0, 1.0]``
        where a higher value means more similar, and results must be sorted by
        descending score.

        This is a hard contract, not a preference. Most vector databases —
        ChromaDB included — natively return a *distance*, where lower means more
        similar; converting it is the adapter's job. An adapter that leaked raw
        distances would invert the relevance threshold in the retriever, and the
        assistant would silently answer using its least relevant chunks while
        escalating the questions it could actually have answered. Nothing would
        crash and no test of the domain would notice.

        Returns an empty sequence when the store holds no chunks.
        """
        ...

    def clear(self) -> None:
        """Remove every stored chunk.

        Used when the documentation is replaced: a stale index would keep
        serving sections that no longer exist, and citations pointing at them
        would be unverifiable.
        """
        ...

    def count(self) -> int:
        """Number of chunks currently stored, for health checks and CLI output."""
        ...


class LLMClient(Protocol):
    """Produces an answer draft from a question and the retrieved context."""

    def generate_answer(
        self,
        question: str,
        context: Sequence[RetrievedChunk],
    ) -> AnswerDraft:
        """Ask the model to answer ``question`` using only ``context``.

        The port speaks the domain's language instead of exposing a generic
        ``complete(prompt) -> str``. Prompt construction and structured-output
        parsing are provider concerns: keeping them inside the adapter means the
        service never assembles prompts, and a second provider cannot quietly
        diverge on how the answer is framed.

        Implementations must not consult any source other than ``context`` — the
        system prompt is where that restriction is enforced. They must also not
        validate the result: an ``AnswerDraft`` is expected to be wrong
        sometimes, and deciding whether its citations hold up is the citation
        validator's job.

        Raises whatever provider error the adapter deems unrecoverable; callers
        treat a failure as "no answer available", never as an empty answer.
        """
        ...
