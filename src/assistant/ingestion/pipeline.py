"""Indexing: documentation in, searchable chunks out.

Four ports in a row — load, chunk, embed, store — and one decision that is not
obvious from the order: **nothing is destroyed until everything has succeeded.**

Reading, chunking and embedding all happen first, in memory. Only once every
vector exists does the pipeline clear the collection and write the new one. A
malformed heading in the last file therefore leaves the previous index intact and
the assistant still answering, instead of wiping a working index and failing
halfway through rebuilding it.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from assistant.domain.models import Chunk
from assistant.domain.ports import DocumentLoader, Embedder, VectorStore, Vector
from assistant.ingestion.chunker import SectionChunker

logger = logging.getLogger(__name__)

# Vector stores cap how much a single write may carry — ChromaDB included. Real
# documentation reaches thousands of chunks, so the write is split rather than
# left to fail on a corpus larger than the demo's.
_UPSERT_BATCH = 500


class IngestionError(RuntimeError):
    """Indexing could not produce a usable index.

    Message written for whoever runs the command, in Italian, like every other
    user-facing string in this project.
    """


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """What was indexed, for the command that has to say so."""

    documents: int
    sections: int
    chunks: int


class IngestionPipeline:
    """Turns whatever the loader finds into an index the retriever can search.

    Every collaborator is a port except the chunker, which is our own policy
    rather than an external dependency. Replacing Markdown with Confluence, or
    ChromaDB with FAISS, changes what is passed to this constructor and nothing
    inside it.
    """

    def __init__(
        self,
        loader: DocumentLoader,
        chunker: SectionChunker,
        embedder: Embedder,
        store: VectorStore,
    ) -> None:
        self._loader = loader
        self._chunker = chunker
        self._embedder = embedder
        self._store = store

    def run(self) -> IngestionReport:
        """Rebuild the index from scratch and report what it now holds.

        Raises:
            IngestionError: if the documentation yields nothing indexable.
            Exception: whatever the loader, embedder or store raise, unwrapped —
                their messages already say what to fix.
        """
        documents = tuple(self._loader.load())
        chunks = tuple(
            chunk for document in documents for chunk in self._chunker.chunk_document(document)
        )
        if not chunks:
            raise IngestionError(
                "La documentazione non ha prodotto alcun blocco indicizzabile.\n"
                "Verificare che i documenti contengano sezioni con un titolo di "
                "secondo livello nella forma '## Titolo {#ancora}'."
            )

        sections = sum(len(document.sections) for document in documents)
        logger.info(
            "Indicizzazione: %d documenti, %d sezioni, %d blocchi",
            len(documents),
            sections,
            len(chunks),
        )

        vectors = self._embedder.embed_documents([chunk.text for chunk in chunks])

        # Only now, with every vector in hand, is the old index touched. Clearing
        # is not optional: a section deleted from the documentation would
        # otherwise stay searchable, and a citation pointing at it could not be
        # verified against anything.
        self._store.clear()
        self._write(chunks, vectors)

        return IngestionReport(
            documents=len(documents), sections=sections, chunks=len(chunks)
        )

    def _write(self, chunks: tuple[Chunk, ...], vectors: Sequence[Vector]) -> None:
        rows = list(vectors)
        for start in range(0, len(chunks), _UPSERT_BATCH):
            stop = start + _UPSERT_BATCH
            self._store.upsert(chunks[start:stop], rows[start:stop])
